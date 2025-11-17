export_zip:
	zip -r greyhound_docx_extractor.zip . -x '*.git*' '*/__pycache__/*' 'outputs/logs/*'
