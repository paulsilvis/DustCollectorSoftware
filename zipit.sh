rm archive.zip
zip -r archive.zip . -x "**.venv/**" -x "**.pio/**" -x "**.git/**" -x "**.obsidian/**" -x "**.pytest_cache/**" -x "AudioCoolness/*" -x "dust_collector_diagrams/**" -x "analysis/**"

