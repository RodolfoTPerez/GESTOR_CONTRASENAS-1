import pytest
from src.presentation.dashboard.voice_search_worker import VoiceSearchWorker

def test_parse_command_basic():
    worker = VoiceSearchWorker()
    assert worker._parse_command("rodolfo@gmail.com") == "rodolfo@gmail.com"
    assert worker._parse_command("busca rodolfo") == "rodolfo"
    assert worker._parse_command("busca correo de rodolfo@gmail.com") == "rodolfo@gmail.com"
    assert worker._parse_command("buscar correo de admin") == "admin"
    assert worker._parse_command("encuentra amazon") == "amazon"

def test_parse_command_case_insensitive():
    worker = VoiceSearchWorker()
    assert worker._parse_command("BUSCA Rodolfo") == "rodolfo"
    assert worker._parse_command("Busca Correo De Admin") == "admin"

def test_parse_command_empty():
    worker = VoiceSearchWorker()
    assert worker._parse_command("") == ""
    assert worker._parse_command("   ") == ""
