# *accel*: A python-based sleep tracker and acoustic brain stimulator built on a Raspberry Pi 💤🔊🧠〰️

*accel* is an unfinished project of building a low-cost sleep tracker and learn a lot on the way. It can track your 💤 sleep during night through an accelerometer and detect how much you are moving. Using this information it then determines whether the user is in the deep sleep (NREM stage II-III) and, if so, trigger the second stage: the acoustic brain stimulation protocol 🔊. This is a low-frequency audible stimulus 〰️ that is then delivered to the 🧠 brain using 🎧 headphones. 

Why trigger the stimulus in deep sleep? It is known that slow wave activity (~1Hz) in the sleeping human cortex is critical for memory consolidation, the process that writes memory from short-term memory to long-term memory [todo:cite]. It has been repeatedly shown [todo:cite] that electrical stimulation of the brain in this sleep stage can enhance memory consolidation in humans. There is also evidence that acoustic stimulation through the auditory cortex can improve memory consolidation as well. 

This project is an experiment to see how far I can approximate the vigorous methods of clinical research with a cheap custom setup that anyone could reproduce. However, it is hard to prove an effect with a subject count of N = 1 at this point. Whether the end goal of enhancing memory consolidation during sleep using an acoustic stimulus can be reached or not, it sure is a fun endeavour! 

## Current build

The hardware and the software is still in very early development. At this stage, the device consists of these parts: a Raspberry Pi Zero W (any other Pi should work), a [MMA8452Q accelerometer chip](https://www.aliexpress.com/wholesale?SearchText=MMA8452Q) (~0.8€) with an I2C interface and a [tiny SSD1306 OLED screen](https://www.aliexpress.com/wholesale?SearchText=ssd1306) (~1.2€), also with an I2C interface. 

The acoustic stimulation is not yet implemented. More literature research is necessary 

![Parts: Raspberry Pi Zero W, MMA8452Q (Accelerometer), SSD1306 (OLED)](resources/partlist.jpg)

You can find all of these parts fairly cheap on the internet. After soldering all the parts together, the "assembled" device is pretty compact and also a bit *shaggy*:

![Assembled device](resources/img12.jpg)

## Data processing

### Sampling data

The data processing is done in multiple steps. The three-dimensional position data x,y,z is sampled from the accelerometer and is used to calculate the time derivative of the position we call dx/dt, giving us a velocity of the sensor. The data is sampled with an adaptive sampling rate: Whenever the velocity crosses a predefined threshold (activity is detected) the sampling rate doubles and we can record the movement with a high precision. The threshold was obtained by visually assessing the noise baseline and setting a threshold slightly above that.

### Simulating the activity model

Whenever the measured movement crosses the threshold, a "spike" of activity is generated. This spike is fed into a very slow model that integrates those spikes in time (it "collects" them) which all ad up to a quantity called "activity". At the same time, the "activity" value always tries to decay back to zero, however slowly, within minutes to tens of minutes. Whenever the activity reaches a pre-defined value close to zero, the sleep stage is classified as "deep sleep".

In deep sleep, the body's movement is reduced to a minimum, so we are trying to decide at every time step if the user hasn't been active for a long-enough time. This slow dynamical model lets us detect slow patterns in the movement activity over a long time scale and helps us decide whether the user hasn't moved for a long time and thus, could be in deep sleep. 

The parameters for this model are chosen manually and haven't been fine-tuned yet. I tried to chose values that consistently have less than 50% of deep sleep and result roughly in two to three "main" deep sleep phases, often occurring in the beginning of the night and at the very end.

![](resources/signal_pipeline.png)

Whenever a very low pre-defined threshold is reached, the user is assumed to be in deep sleep. In this stage, the audio stimulus is triggered.

### Generating the audio stimulus

The slow oscillations in slow-wave sleep or deep sleep are typically around a frequency of 0.75Hz (this is a very broad generalisation. There is inter- and intra-subject variability of the oscillation frequency). As a crude approximation, we will use this frequency for audio input to the user. The human ear cannot perceive much below 20Hz and most headphones stop to work around that frequency for that reason. What we can do, however, is to mix two audible frequencies (base frequency) of, say, 40Hz and 40.75Hz. The small difference between the signals will cause a slow beating sound at the frequency of 0.75Hz. Assuming that neuronal activity in the auditory cortex is resonant to these frequencies, we hope that oscillatory energy input to the brain can entrain or amplify ongoing slow-wave activity.

In the plot below, a impractically low base frequency of 8Hz and a difference of 0.75 is chosen here for illustration purpose. You see a stimulus that lasts for around 7 seconds. 

![](resources/audio_input.png)

### A typical night

Here is what a typical night looks like with the current integrator. The red spikes represent movements, the blue shaded area is the integrated level of activity. Periods when the activity drops close to zero are classified as periods of "deep sleep".

![](resources/sleep.png)

## Getting started

First, I want to thank all the people who made all the modules and libraries that I could use to make this project possible. It is amazing what kind of amazing possibilities can lie just one pip install away. The drivers for the accelerometer and the OLED screen are snippets I found online and haven't yet documented where they are from (oops). Thanks also to their authors! 

This project is based on some debian and a python packages. Please make sure that you have installed them. The following commands should work for a fresh install of Raspbian Buster Lite. Make sure you set up ssh correctly and connect to a network ([Google search](https://www.google.com/search?q=raspberry+pi+zero+w+headless+setup)).

### Enable I2C interface
This is the hardware interface that lets you communicate to connected chips. Enter 

```
sudo raspi-config
``` 

and go to --> `Interfacing` --> `Enable I2C`
### Install python3 and other binaries
```
sudo apt update -y
sudo apt install build-essential python3-dev python3-pip libatlas-base-dev libhdf5-dev i2c-tools git -y
```
Set python3 as your default python

```
sudo update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2
sudo ln -s /usr/bin/pip3 /usr/bin/pip

```
### Install python packages

```
pip install -r requirements.txt
```
This also installs the `h5py` package for logging data to the disk, `redis` for streaming the data to a redis server and `flask` for the web interface. These functions are optional but make sure to edit the `config.py` file accordingly.

For the OLED display to work you need to install the Pillow library that is used to paint the image. (Note that compiling Pillow on the RPi zero is painfully slow...)

```
sudo apt install libjpeg-dev -y
pip install Pillow
```

You should be all set up at this point 👍.

### Determine I2C addresses of connected devices

In order to talk to the accelerometer and the OLED display, you need to find out what their addresses are. You can then put these into the `config.py` file in the root directory of this repository. The default values in there might work as well!

```
sudo i2cdetect -y 1
```
The output should look something like

![](resources/i2cdetect.png)

Here, my accelerometer has the address `0x1d` and the OLED `0x3c`. Good to know! Put these values into `config.py`. (Note: I don't know how you can know which is which at this stage).

### Run the tracker

To execute the script, run
`python accel.py`.

If you did everything I did, you should be able enable autostart of this script using the command below.

```
echo "sudo -u pi /usr/bin/python /home/pi/accel/accel.py &" | sudo tee -a /etc/rc.local
```
## Project roadmap
* [✓] Receive raw movement data from accelerometer
* [✓] Build dynamical model for activity level
* [✓] Save data to local hdf file
* [✓] Save data to remote redis server
* [✓] Plot live movement data to OLED display
* [✗] Design acoustic stimulus 
* [✗] Build a hard case for the tracker
* [✗] Assess deep-sleep detection accuracy using simultaneous sleep EEG
* [✗] Trigger acoustic stimulus in deep sleep
* [?] Use wireless EEG for sleep stage detection *somewhen in the far far future*

## Neuroscience background (wip)

Integrated circuits with *I2C interfaces*, cheap linux computers like the *Raspberry Pi* and modular programming languages with a strong open source community like *python* enable everyone to build their own mobile sensory devices like never before. This is an educational project that helped me learn all sorts of things, based on a personal scientific research project. In this repository, I will describe the ideas and process behind building a sleep tracker that will trigger a stimulus in deep sleep.

### What is deep sleep?
Human sleep is divided into sleep cycles, usually 3-4 cycles in a full night of sleep. Each cycles has a number of sleep stages, each with their own distinct brain activity signature as measured in electroencephalography (EEG). Below is a plot from [Onton et al, Front. Hum. Neurosci. (2016)](https://www.frontiersin.org/articles/10.3389/fnhum.2016.00605/full) showing EEG power spectra and a *Hypnogram* that segments sleep into different sleep stages.

![Onton et al, Front. Hum. Neurosci. (2016)](resources/Onton2016.jpg)

Here, it is evident that the dominant frequency (most prominent frequency in the EEG power spectrum) in deep sleep is around and below 1 Hz. This stage is also referred to as **slow-wave sleep (SWS)** and the low-frequency activity is often called slow-wave activity (SWA) or slow-wave oscillations (SWO). Is is known that these slow oscillations that are most likely generated in the neocortex are key for successful memory consolidation during sleep. Simply said, memory consolidation is the process with which the brain transfers memories (encoded as *engrams*) from its short-term memory storage (believed to be in Hippocampus) to the long-term memory storage (in neocortex).

We want to detect the deep sleep stage during night (referred to as HI DEEP and LO DEEP in the plot above) and trigger an action whenever it is detected.

## License
This project is licensed under the MIT License.