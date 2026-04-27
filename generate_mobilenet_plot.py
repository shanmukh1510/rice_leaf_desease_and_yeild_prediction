import json
import re
import matplotlib.pyplot as plt

with open('leaf_disease.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

text_lines = []
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if 'history = model.fit(' in source and 'EPOCHS' in source:
            outputs = cell.get('outputs', [])
            if outputs and 'text' in outputs[0]:
                text_lines = outputs[0]['text']
                break

epochs = []
acc = []
loss = []
val_acc = []
val_loss = []

epoch_pattern = re.compile(r'Epoch (\d+)/\d+')
metrics_pattern = re.compile(r'accuracy: ([\d.]+) - loss: ([\d.]+) - val_accuracy: ([\d.]+) - val_loss: ([\d.]+)')

for line in text_lines:
    ep_match = epoch_pattern.search(line)
    if ep_match:
        epochs.append(int(ep_match.group(1)))
    
    met_match = metrics_pattern.search(line)
    if met_match:
        acc.append(float(met_match.group(1)))
        loss.append(float(met_match.group(2)))
        val_acc.append(float(met_match.group(3)))
        val_loss.append(float(met_match.group(4)))

plt.figure(figsize=(12, 5))

# Accuracy plot
plt.subplot(1, 2, 1)
plt.plot(epochs, acc, label='Training Accuracy', marker='o')
plt.plot(epochs, val_acc, label='Validation Accuracy', marker='o')
plt.title('MobileNetV2 Accuracy over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

# Loss plot
plt.subplot(1, 2, 2)
plt.plot(epochs, loss, label='Training Loss', marker='o')
plt.plot(epochs, val_loss, label='Validation Loss', marker='o')
plt.title('MobileNetV2 Loss over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('mobilenet_training_plot.png')
print("Plot saved as mobilenet_training_plot.png")
