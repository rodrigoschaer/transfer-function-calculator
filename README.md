# Circuit Transfer Function Calculator

This project is an application for calculating transfer functions of small signal model of transistors.

# Usage

To run the application, follow these steps:

1. Install the required dependencies using `pip install -r requirements.txt`.
2. Run main application with `python3 main.py`

# Current and next steps

At first a got a little bit ahead of myself and underestimated the complexity for the app's core main task, now I'm starting fresh from the basics:
- [x] Get a transfer function small signal model amplifier circuit

Next steps:

- [ ] Find a way of putting the answer in a polynomial format;
- [ ] Create a way of passing the analyzed circuit via spice file;
- [ ] Maybe make a LTSpice plugin (this one is really long term)

# How to Setup this project

Run the following commands:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## License

This project is licensed under the MIT License.
