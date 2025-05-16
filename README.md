## Python Solution Architecture
```
┌─────────────────┐     ┌───────────────────┐     ┌────────────────┐
│ Input Handler   │     │ Business Logic    │     │ API Client     │
│ - Device Reader │────>│ - Barcode Parser  │────>│ - Grocy API    │
│ - Event Listener│     │ - Action Resolver │     │ - OurGroceries │
└─────────────────┘     └───────────────────┘     └────────────────┘
        │                        │                        │
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐     ┌───────────────────┐     ┌────────────────┐
│ Configuration   │     │ Feedback System   │     │ Logging        │
│ - Settings      │     │ - Audio           │     │ - Activity Log │
│ - Mappings      │     │ - LED/Display     │     │ - Error Log    │
└─────────────────┘     └───────────────────┘     └────────────────┘

```
### Implementation Notes

This utility makes it possible to have a "headless" scanner inputting data into Grocy. With no need to keep your phone or computer available, no need to pull up an app or website, it's easier to just get a quick scan for your daily consumption or quickly go through your inventory looking for things to refresh before heading to the store. 

Get your scanner commands, product groups, quantity units and locations set up as barcodes with the barcode_generator util. See the README at ./barcode_generator/README.md for more info.

### Class Definitions

1. BarcodeScanner Class (barcode_scanner.py)
   • Handles input from barcode scanners in different connection modes
   • Currently focuses on USB HID mode using evdev
   • Includes methods for device detection, event processing, and barcode decoding

2. GrocyClient Class (grocy_client.py)
   • Provides a complete interface to the Grocy API
   • Includes methods for product lookup, inventory management, and shopping lists
   • Handles authentication and error handling

3. BarcodeProcessor Class (barcode_processor.py)
   • Processes scanned barcodes and determines appropriate actions
   • Supports action mapping based on barcode prefixes
   • Executes actions like consume, purchase, or adding to shopping lists

4. FeedbackManager Class (feedback_manager.py)
   • Provides user feedback through audio and visual means
   • Supports different feedback types (shopping, error, consume)
   • Uses pygame for audio feedback (optional)

5. ConfigManager Class (config_manager.py)
   • Loads configuration from YAML files
   • Supports environment variable overrides
   • Provides access to different configuration sections

6. BarcodeApp Class (main.py)
   • Main application class that ties everything together
   • Handles initialization, signal handling, and cleanup
   • Implements the main application loop


### Installation
`cp .env.example .env && nano .env`
Create an API token in your Grocy app and drop it into the .env file

Review the docker-compose.yml file for anything that needs to change for your instance, for example if you are using a HID scanner then you will want to discover which event to listen for on your host and mount that event folder to your container. Try `cat /proc/bus/input/devices`, find your device and look at the Handlers sectio for the proper event

`docker-compose up -d --build`

`tail -f --lines=5 logs/barcode_scanner.log`

That's all there should be to it - the app runs by default and listens to that event for barcode input. If you don't have a barcode already, feel free to get the one I got (Inateck BCST-21). It cost around $50 for the 2D version (allowing for QR code scanning). I have this app running on a mini server and the HID Wireless port is plugged into that box, making the events listenable.


## Inateck BCST-21 Barcode Scanner Capabilities

The BCST-21 Bluetooth barcode scanner has these key features:
• Supports both Bluetooth and USB wired connections
• Can operate in HID (Human Interface Device) mode, which makes it function like a keyboard
• Has a 100m Bluetooth transmission range
• Supports multiple barcode formats (1D/2D)
• Has internal memory for offline scanning
• Comes with SDK/APP support for custom integration
• Can be configured through scanning special barcodes in the manual

Native interfaces:
1. USB HID mode - appears as a keyboard device when connected via USB
2. Bluetooth HID mode - pairs as a keyboard device
3. SPP (Serial Port Profile) mode - can be configured to work as a serial device
4. SDK interface - for more advanced integration


## To integrate with Home Assistant so Home Assistant reads your barcode status updates


In docker-compose.yml, add the scanner log to your volumes (of course, use your own path here) so that the file can be read by HomeAssistant:
```
    volumes:
      - /home/{user}/codebases/grocy_scanner_util/logs:/scanner_logs:ro
```


At the bottom of config/configurations.yml, add your command line sensor:
```
command_line:
  - sensor:
      name: 'Barcode Scanner Log'
      command: 'tail -n 1 /scanner_logs/barcode_scanner.log'
      scan_interval: 5
      unique_id: barcode_scanner_log
      value_template: '{{ value.split("::")[1] }}'
```


In config/automations.yml - you will need to get the entity ID of your own media player from your /config/entities page in HomeAssistant:
```
- id: '1747108084155'
  alias: Speak Barcode Log on Update
  description: Speak the last line of the barcode scanner log on the selected media player.
  triggers:
  - entity_id: sensor.barcode_scanner_log
    trigger: state
  conditions: []
  actions:
  - target:
      entity_id:
      - tts.google_translate_en_com
    data:
      media_player_entity_id: media_player.dining_room
      message: '{{ states(''sensor.barcode_scanner_log'') }}'
      cache: false
    action: tts.speak
  mode: single
```

I have limited understanding of HomeAssistant but this worked for me!

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request or make a feature request, or you can also drop "appreciation" at http://buymeacoffee.com/erinalbers if you want your contribution to be more... inspirational.