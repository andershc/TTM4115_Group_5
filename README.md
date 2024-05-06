# TTM4115_Group_5
## Project for group 5

The main vision of our solution is to allow electric vehicle drivers to plan their drive ahead, without having to physically check the stations. We start from an already functioning system and envision an app for the users, where we implement new features linked to the charging stations. This includes a clear overview of available and operational chargers, as well as which chargers are defective at the station. The app will, based on these parameters, provide an estimated waiting time for the customers, which gives a rough and dynamic overview of how busy the charging station is at a time. For customers physically at the station, a lamp indicating the status of the charger will be implemented.

This is a prototype with three main components serving as a proof of concept for our vision.

### Webapp

The webapp is created with nextjs app router and uses noth TypeScript and Tailwind-CSS. To run the application do the following:

1. Clone the repository: ``git clone https://github.com/your-username/TTM4115_Group_5.git``
2. Navigate to the frontemd: ``cd frontend/electric-charger-app``
3. Install the required dependencies: ``yarn install``
4. Start the application: ``yarn run dev``

### Server

The server is mainly an MQTT server with an HTTP aspect for some user management.

To run the server navigate to /server and run the ``server.py`` file.

### Pi

The charging station is represented by a program running on a Raspberry Pi. Run the program on a pi by navigating to /raspberryPi and run the ``chargerFirmware.py`` file.
