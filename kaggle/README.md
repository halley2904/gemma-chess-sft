# Kaggle workflow

1. Create a Kaggle Notebook and enable GPU in Notebook Settings.
2. Check exact GPU model, quota, RAM and writable storage in your account.
3. Attach a versioned input dataset or use a small source sample.
4. Clone this repository or use Kaggle's built-in GitHub linking.
5. Run environment/data checks before training.
6. Save checkpoints and intermediates under `/kaggle/working`.
7. Export outputs as a versioned Kaggle Dataset or notebook output; do not commit checkpoints to Git.

Kaggle quotas and accelerator availability can change. The live account UI is authoritative; do not assume a fixed GPU or weekly quota.

Official docs:
- https://www.kaggle.com/docs/notebooks
- https://www.kaggle.com/docs/efficient-gpu-usage
- https://github.com/Kaggle/kaggle-cli
