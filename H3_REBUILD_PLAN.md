# Dolorain Studio — MiniMax H3 / Original ComfyUI

## लक्ष्य
Vast.ai के तैयार CUDA/PyTorch वातावरण पर Original ComfyUI चलाना; Custom Studio UI या निजी Docker Image आवश्यक नहीं।

## आवश्यक फ़ाइलें
- `workflows/01_Character_Sheet_Designer.json`
- `workflows/02_H3_Video_Generation.json`
- ComfyUI Custom Nodes की reproducible install सूची
- Vast.ai के लिए setup, update, verify और startup scripts
- Models को Vast.ai पर डाउनलोड करने की अलग प्रक्रिया; weights GitHub में नहीं रखेंगे

## बदलाव और परीक्षण
1. `h3-comfyui-rebuild` Branch पर पुरानी Cloud सामग्री का replacement तैयार करना।
2. Vast.ai पर GPU सहित ComfyUI, nodes, workflow loading और H3 generation की जाँच।
3. उपयोगकर्ता की मंजूरी के बाद ही `main` Branch को बदलना।

## स्थिति
यह केवल तैयारी का दस्तावेज़ है। अभी पुरानी main Branch नहीं बदली गई है। मौजूदा Dockerfile को सीधे Vast.ai setup script समझकर न चलाएँ।
