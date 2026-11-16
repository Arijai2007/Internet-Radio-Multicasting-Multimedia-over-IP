from dataclasses import replace
import tkinter as tk
import pytest
from radio.core import load_stations, save_stations
from radio.app import RadioApp
from radio.editor import ChannelEditor


def test_atomic_save_roundtrip_and_invalid_update(tmp_path):
    path = tmp_path / 'stations.json'
    stations = load_stations()
    save_stations(stations, path)
    assert load_stations(path) == stations
    original = path.read_bytes()
    with pytest.raises(ValueError):
        save_stations([stations[0], stations[0]], path)
    assert path.read_bytes() == original


def test_editor_add_edit_choose_media_and_remove(tmp_path, monkeypatch, tk_root):
    from radio import editor
    root = tk.Toplevel(tk_root)
    root.withdraw()
    path = tmp_path / 'stations.json'
    save_stations(load_stations(), path)
    def apply(stations):
        save_stations(stations, path)
        return True
    window = ChannelEditor(root, load_stations(path), apply)
    try:
        media = tmp_path / 'my song.wav'
        media.write_bytes(b'file selection test')
        monkeypatch.setattr(editor.filedialog, 'askopenfilename', lambda **kw: str(media))
        window.fields['name'].set('My songs')
        window.browse()
        window.save()
        root.update()
        assert len(load_stations(path)) == 3
        assert load_stations(path)[2].source == str(media)
        window.tree.selection_set('2')
        window.select()
        window.fields['name'].set('Renamed')
        window.save()
        root.update()
        assert load_stations(path)[2].name == 'Renamed'
        monkeypatch.setattr(editor.messagebox, 'askyesno', lambda *a, **kw: True)
        window.tree.selection_set('2')
        window.select()
        window.remove()
        assert len(load_stations(path)) == 2
    finally:
        window.destroy()
        root.destroy()


def test_app_applies_local_edits_without_saving_remote_channels(tmp_path, monkeypatch, tk_root):
    import radio.app as module
    path = tmp_path / 'stations.json'
    monkeypatch.setattr(module, 'save_stations', lambda stations: save_stations(stations, path))
    root = tk.Toplevel(tk_root)
    root.withdraw()
    app = RadioApp(root)
    try:
        app.stations = [replace(app.local_stations[0], name='Remote channel')]
        updated = [replace(app.local_stations[0], name='Local edit')]
        assert app.apply_channels(updated)
        assert load_stations(path) == updated
        assert app.stations == updated
        assert app.local_stations == updated
    finally:
        app.close()
