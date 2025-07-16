# whatplane?

A Python Tkinter app that shows real-time flight information overhead for a specified location using the Flightradar24 public API.

## Setup

1. Clone the repo and `cd` into the directory.
2. Create a virtual environment:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set your bounding box in `.env`:
   ```
   BOUNDS_BOX=64.5,64.3,-5.3,-5.0
   ```
5. Run the app:
   ```
   python app.py
   ```

## Notes

- This app uses an unofficial Flightradar24 API and may be rate-limited.
- On macOS, Tkinter UI may be blank due to system Tk issues. Use python.org Python for best results.
