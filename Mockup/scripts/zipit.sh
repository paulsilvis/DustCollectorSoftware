zip -r dustcollector_mock_state_20251226_0530.zip \
    src config run.sh scripts/run.sh \
    -x "*/__pycache__/*" "*.pyc" ".venv/*"
