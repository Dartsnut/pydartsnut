# pydartsnut
The python module work with Dartsnut hardware.

## Installation

```bash
pip install pydartsnut
```

## Usage

### Initialize the module

```python
from pydartsnut import Dartsnut

dartsnut = Dartsnut()
```

### Retrieve user input parameters

```python
params = dartsnut.widget_params
# Returns a dictionary of current widget parameters.
print(params)

# Safely get the city name from params
city_name = ""
if params is not None:
	city_name = params.get("city", "")
if city_name == "":
	# TODO: assign default value or show a warning image
    pass
```

### Update the frame buffer for display

```python
from PIL import Image

image = Image.open("your_image.png")
dartsnut.update_frame_buffer(image)
# Or using a bytearray (RGB888 format)
dartsnut.update_frame_buffer(bytearray_data)
```

### Get darts positions

```python
darts = dartsnut.get_darts()
# Returns a list of 12 [x, y] coordinates.
# [-1, -1] means the dart is not present.
```

### Get button states

```python
buttons = dartsnut.get_buttons()
# Returns a dictionary:
# {
#     "btn_a": False,
#     "btn_b": False,
#     "btn_up": False,
#     "btn_right": False,
#     "btn_left": False,
#     "btn_down": False,
#     "btn_home": False,
#     "btn_reserved": False,
# }
```