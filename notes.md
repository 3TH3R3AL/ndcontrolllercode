
- Only run the mhv on channel 1
- Only run other three (caen) on channel 0+1+2
- isnap-srv3.phys.nd.edu
- ADND/omorelan
- Normal password
- SSH is rms@stgcontrol1.phys.nd.edu
- Password is saved
- Remember to sign out
- Meet july 20th 3:30
## Goals
- Code that fingerprints usbs
- Get preset values save them and don't change them (except for channel 1 and 2 of serial 1283, but don't go higher than 100v on those)
- Turn channel on and off
- Interface with labview (with heartbeat)
- All but 4th on MHV4
- Use Caen with 0V presets
- Parallel, clean stop, initialization
0. Caen 1283
1. MSCF-16 Amplifier thing
2. Caen 2
3. Caen 3
4. MHV4

- Visual for waiting for mhv4 and stuff
- Capture content of json file, load standard setup button 
- Make a way to set specific voltages 
- Make tabs to hide behind the scenes
- Double check compatibiliyt with labview 15
- Meet earlier next tuesday
- Set current limit MHV4
- Bootup loading animation
- 1pm next tuesday
- Add preset values display to set values
- Email or wait til saturday to talk about next tuesday
- Keep mhv4 below 5v