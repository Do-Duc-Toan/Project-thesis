# Hardware
+ Compatible with STM32Cube IDE version 1.15.1.
+ The main microcontroller board utilized in this project is STM32F446RE NUCLEO
+ Recommend to use ESP8266 for communication part.

# MQTT
+ MQTT Mosquitoo

# Simulator
### How to run
**I. Activate virtual environment**
+ Clone the repo ***AGV simulator***
+ Ensure all the files in a same folder
+ Install packages in requirements.txt
   
**II. Activate your MQTT broker**
+ Change your server address in the files named ***agv_simulator.ipynb*** (cell 3, line 16) and ***agv_controller.py*** (if necessary)
+ You can change your topics in file ***agv_mqtt.py*** (in the `class AGVMQTTClient`)
+ Open the Command Prompt, change the directory to `C:\Program Files\mosquitto>` then enter this command `mosquitto_sub -h localhost -t "agv_data/#" -v` (change the topic tailored with your system). This command is used to track the data sent from the simulator
+ The file ***agv_controller*** is just a file to test the data sending/receiving process from simulator. You can also manually type some command to control the simulator (type 1 to control the agv 1, ...)

**III. Run the simulator**
+ You can change the initial positions of 3 agvs in the last cell of the file `afv_simulator.ipynb` : 
  + `car_initial_config_data = [ 
            {'id': 1, 'start_node': 7, 'color': 'red'},
            {'id': 2, 'start_node': 17, 'color': 'blue'},
            {'id': 3, 'start_node': 32, 'color': 'green'}
        ]`

+ Run the simulator (simply click the **Run All** button on the top)
+ Check whether the data is transmitted successfully (in *Command Prompt* or the Terminal of the *file agv_controller.py*). If not, check your broker address (IP adress) and your topics again.




