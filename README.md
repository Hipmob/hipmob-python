hipmob-python
=============

Hipmob Python bindings

## Installation

Download the latest version of the Hipmob server API Python bindings with:

    git clone https://github.com/Hipmob/hipmob-python

To get started, add the following to your Node file:

   import hipmob

Simple usage looks like:

       hm = hipmob.Hipmob("your-username", "your-apikey")
       apps = hm.get_applications()
       if apps == None:
       	  print "No applications were found."
       else:
		for app in apps:
		    print app

## Documentation

Please see https://www.hipmob.com/documentation/api.html for detailed documentation.
