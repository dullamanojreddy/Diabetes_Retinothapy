# Model Weights Directory

Place the trained PyTorch EfficientNet-B3 checkpoint here:

- **Filename**: `best_efficientnet_b3.pth`
- **Expected Size**: ~123 MB
- **Architecture**: EfficientNet-B3 with 5-class linear classification head
- **State Dict Structure**:
  - `epoch`: int
  - `model_state_dict`: dict
  - `optimizer_state_dict`: dict
  - `scheduler_state_dict`: dict
  - `val_macro_f1`: float
  - `val_loss`: float
