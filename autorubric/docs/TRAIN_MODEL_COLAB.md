# Colab Training Guide for AutoRubric Evaluator

*Note: Until this process is completed, AutoRubric evaluates submissions using a lightning-fast lexical heuristic fallback (`mock` backend). To unlock true semantic grading, you must fine-tune the RoBERTa-large model.*

## 1. Open the Notebook
1. Open Google Colab (https://colab.research.google.com).
2. Upload the notebook located at `ml/notebooks/train_colab.ipynb` from this repository.

## 2. Set Up the GPU Environment
1. In Colab, go to **Runtime** > **Change runtime type**.
2. Select **T4 GPU** (available on the free tier).
3. Click **Save**.

## 3. Run the Training
1. Select **Runtime** > **Run all**.
2. The notebook will automatically:
   - Install dependencies (`transformers`, `datasets`, `torch`).
   - Download the SciEntsBank dataset and apply the 4-way label mapping.
   - Fine-tune `RoBERTa-large` for sequence-pair classification.
3. **Expected Runtime:** ~20-30 minutes on a T4 GPU.
4. **Expected Metrics:** Macro-F1 should rise significantly above the baseline 0.375, generally reaching 0.70 - 0.85 depending on hyperparameter tuning.

## 4. Download and Install the Weights
1. Once training finishes, the notebook will save the final model weights into a directory (usually `/content/checkpoint/`).
2. Download these files (specifically `config.json`, `pytorch_model.bin` or `model.safetensors`, and the tokenizer files).
3. On your local machine, place all these files into the `ml/checkpoint/` folder in the AutoRubric project root.

## 5. Activate the Model
1. Open your `.env` file in the `backend/` folder.
2. Set the evaluator backend to run on the CPU (or GPU if you have one locally):
   ```env
   EVALUATOR_BACKEND=cpu
   ```
3. Start the backend: `docker compose up -d`
4. Confirm activation by hitting the health endpoint: `GET http://localhost:8000/health/ready`. The JSON response should show `"backend": "cpu"` and `"weights_present": true`.
