$env:MSYSTEM=''
$env:PYTHONUTF8='1'
$env:ESP_IDF_VERSION='6.1.0'
$env:IDF_PATH='C:\esp\v6.1\esp-idf'
$env:IDF_PYTHON_ENV_PATH='C:\Users\priya\.espressif\python_env\idf6.1_py3.10_env'
& 'C:\Users\priya\.espressif\python_env\idf6.1_py3.10_env\Scripts\python.exe' 'C:\esp\v6.1\esp-idf\tools\idf.py' @args
exit $LASTEXITCODE