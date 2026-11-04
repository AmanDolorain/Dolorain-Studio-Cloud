import os
from aiohttp import BasicAuth
import unittest
from unittest.mock import patch
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestClient, TestServer
import app as studio


class CloudBrowserTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async def engine(req):
            if req.path == '/system_stats':
                return web.json_response({'devices': []})
            if req.path == '/ws':
                ws = web.WebSocketResponse()
                await ws.prepare(req)
                msg = await ws.receive()
                await ws.send_bytes(msg.data)
                return ws
            return web.Response(body=(await req.read()) or b'native response')
        fake = web.Application()
        fake.router.add_route('*','/{path:.*}', engine)
        self.engine = TestServer(fake)
        await self.engine.start_server()
        self.addAsyncCleanup(self.engine.close)
        address = patch.object(studio,'ENGINE', str(self.engine.make_url('/')).rstrip('/'))
        address.start()
        self.addCleanup(address.stop)
        env = patch.dict(os.environ, DSC_STUDIO_PASSWORD='unit-test-secret-123456')
        env.start()
        self.addCleanup(env.stop)
        app = web.Application(middlewares=[studio.access])
        session = ClientSession()
        self.addAsyncCleanup(session.close)
        app['client'] = session
        app.router.add_route('*','/{path:.*}',studio.handle)
        self.browser = TestClient(TestServer(app),auth=BasicAuth('studio','unit-test-secret-123456'))
        await self.browser.start_server()
        self.addAsyncCleanup(self.browser.close)

    async def test_native_access(self):
        self.assertIn('Dolorain Studio',await (await self.browser.get('/')).text())
        self.assertEqual(await (await self.browser.get('/?studio_canvas=1')).text(),'native response')
        self.assertEqual((await self.browser.get('/extensions/audio/player.js')).status,200)
        self.assertEqual(await (await self.browser.post('/upload/image',data=b'image')).read(),b'image')
        async with self.browser.ws_connect('/ws') as ws:
            await ws.send_bytes(b'preview')
            self.assertEqual((await ws.receive()).data,b'preview')
        with patch.dict(os.environ, DSC_STUDIO_PASSWORD='another-long-password-12345'):
            self.assertEqual((await self.browser.get('/')).status,401)

    async def test_diagnostics(self):
        graph={'nodes':[{'id':1}],'links':[[1,1,0,2,0,'IMAGE']]}
        r=await self.browser.post('/_studio/diagnostics',json=graph)
        layers=(await r.json())['layers']
        self.assertIn('missing node',layers['Studio adapter'])
        self.assertIn('PASS',layers['Bounded transport'])
        self.assertIn('NOT CONNECTED',layers['Backend adapter'])
        self.assertIn('READY',layers['ComfyUI backend'])
        await self.engine.close()
        layers=(await (await self.browser.get('/_studio/diagnostics')).json())['layers']
        self.assertEqual('UNAVAILABLE',layers['ComfyUI backend'])

    async def test_startup_log(self):
        await studio.run_child('test',[studio.sys.executable,'-c',"print('[FAILED] GPU probe failed')"])
        studio.note('test','token=example-private-value')
        recent='\n'.join(studio.EVENTS)
        self.assertIn('GPU probe failed',recent)
        self.assertNotIn('example-private-value',recent)
