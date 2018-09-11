# List of all possible Lupusec devices

## Alarm Control Panel
- XT 1
- XT1 Plus
- XT 2 
- XT 2 Plus
- XT3

## Sensors
- Door and window contact (binary)
- Movement sensor (binary)
- Movement sensor dual way
- Smokedetector
- Shock sensor
- Water detector
- Glass shatter sensor
- Temperature (const)
- Lightsensor (const)

## Camera
- Lupusnet HD 203 (night)
- Lupusnet HD 201 (outdoor)
- Lupusnet HD 971 (outdoor, rotatable, night)
- Lupusnet HD 934 (outdoor night)
- Lupusnet HD 969 (night)

## Keypads
- Lupusec Keypad V2

## Sirens
- Lupusec Outer siren V2
- Inner siren

## Buttons
- Panic button
- Emergency button

## Covers
- Coverrellais

## Power plugs
- RC powerplug


http://192.168.2.153/action/panelCondGet

response:

/*-secure-
{	updates : {
		mode_st : "Disarm",
		alarm_ex : "Normal",
		battery : "Normal",
		battery_ex : "Normal",
		dc_ex : "Geschlossen",
		tamper : "Geschlossen",
		interference : "Normal",
		ac_activation : "Normal",
		rssi : "1"
	},
	forms : {
		pcondform : {
			mode : "2"
		}
	}
}
*/

http://192.168.2.153/action/sensorListGet

/*-secure-{
   senrows:[
      {
         no:"1",
         type:"Türkontakt",
         zone:"1",
         name:"WZ-Ost",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"2",
         type:"Türkontakt",
         zone:"2",
         name:"WZ-Süd-1",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"3",
         type:"Türkontakt",
         zone:"3",
         name:"WZ-Süd-2",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"4",
         type:"Türkontakt",
         zone:"4",
         name:"Küche-Ost",
         attr:"Eingangsbereich",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"5",
         type:"Türkontakt",
         zone:"5",
         name:"Haustür",
         attr:"Eingangsbereich",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"6",
         type:"Türkontakt",
         zone:"6",
         name:"Bad",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"7",
         type:"Keypad",
         zone:"7",
         name:"Keypad",
         attr:"",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"8",
         type:"Wassermelder",
         zone:"8",
         name:"H2O Keller",
         attr:"",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"9",
         type:"Türkontakt",
         zone:"9",
         name:"Küche-Nord",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"10",
         type:"Türkontakt",
         zone:"10",
         name:"Keller_HWR",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"11",
         type:"Türkontakt",
         zone:"11",
         name:"Keller_AR",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"12",
         type:"Türkontakt",
         zone:"12",
         name:"Keller_WZ",
         attr:"Home Entry",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"13",
         type:"Aussensirene",
         zone:"13",
         name:"Sirene",
         attr:"",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"14",
         type:"Rauchmelder",
         zone:"14",
         name:"Fire-Gas",
         attr:"",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      }
   ]
}*/

http://192.168.2.153/action/panelCondPost

parameter: {mode: 1} //Home
parameter: {mode: 2} //Disarm
parameter: {mode: 0} //Arm


/*-secure-
{	senrows : [
{no : "1", type : "Türkontakt", zone : "1", name : "Eingang", attr : "Eingangsbereich", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "2", type : "Keypad", zone : "2", name : "Eingang", attr : "",cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "3", type : "Türkontakt", zone : "3", name : "HW rechts", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "4", type : "Türkontakt", zone : "4", name : "HW links", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "5", type : "Türkontakt", zone : "5", name : "Gäste WC", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "6", type : "Türkontakt", zone : "6", name : "Küche Ost", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "7", type : "Türkontakt", zone : "7", name : "Küche Süd", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "8", type : "Türkontakt", zone : "8", name : "WZ Süd", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "9", type : "Türkontakt", zone : "9", name : "WZ 1", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "10", type : "Türkontakt", zone : "10", name : "WZ 2 Tür", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "11", type : "Türkontakt", zone : "11", name : "WZ 3", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "12", type : "Türkontakt", zone : "12", name : "WZ 4", attr : "Einbruch", cond : "", battery : "", tamp : "", bypass : "Inaktiv"},
{no : "13", type : "Bewegungsmelder", zone : "13", name : "Flur", attr : "Home Modus", cond : "", battery : "", tamp : "", bypass : "Inaktiv"}]
}
*/



/*-secure-{
   senrows:[
      {
         no:"1",
         type:"Türkontakt",
         zone:"1",
         name:"Eingang",
         attr:"Eingangsbereich",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"2",
         type:"Keypad",
         zone:"2",
         name:"Eingang",
         attr:"",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"3",
         type:"Türkontakt",
         zone:"3",
         name:"HW rechts",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"4",
         type:"Türkontakt",
         zone:"4",
         name:"HW links",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"5",
         type:"Türkontakt",
         zone:"5",
         name:"Gäste WC",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"6",
         type:"Türkontakt",
         zone:"6",
         name:"Küche Ost",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"7",
         type:"Türkontakt",
         zone:"7",
         name:"Küche Süd",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"8",
         type:"Türkontakt",
         zone:"8",
         name:"WZ Süd",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"9",
         type:"Türkontakt",
         zone:"9",
         name:"WZ 1",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"10",
         type:"Türkontakt",
         zone:"10",
         name:"WZ 2 Tür",
         attr:"Einbruch",
         cond:"Offen",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"11",
         type:"Türkontakt",
         zone:"11",
         name:"WZ 3",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"12",
         type:"Türkontakt",
         zone:"12",
         name:"WZ 4",
         attr:"Einbruch",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      },
      {
         no:"13",
         type:"Bewegungsmelder",
         zone:"13",
         name:"Flur",
         attr:"Home Modus",
         cond:"",
         battery:"",
         tamp:"",
         bypass:"Inaktiv"
      }
   ]
}*/


/*-secure-{
   forms:{
      pssform1:{
         ch:1,
         name:"Kanal xy",
         ready:1,
         pssonoff:1
      },
      pssform2:{
         ch:2,
         name:"Kanal 2",
         ready:0,
         pssonoff:1
      },
      pssform3:{
         ch:3,
         name:"Kanal 3",
         ready:0,
         pssonoff:1
      },
      pssform4:{
         ch:4,
         name:"Kanal 4",
         ready:0,
         pssonoff:1
      },
      pssform5:{
         ch:5,
         name:"Kanal 5",
         ready:0,
         pssonoff:1
      },
      pssform6:{
         ch:6,
         name:"Kanal 6",
         ready:0,
         pssonoff:1
      },
      pssform7:{
         ch:7,
         name:"Kanal 7",
         ready:0,
         pssonoff:1
      },
      pssform8:{
         ch:8,
         name:"Kanal 8",
         ready:0,
         pssonoff:1
      }
   }
}*/