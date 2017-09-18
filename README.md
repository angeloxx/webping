# Introduction
This is a script used in my side-activity (www.range-id.it) to detect an unwanted change of a web page, even if it is protected by ModSecurity and best-in-class ruleset. This script takes a screenshot of the webpage and check if an area is changed. This script is based on nodejs (for the screenshot part), python (the glue and image resize, you can rewrite it in bash) and imagemagick for the image match.
This script is used as a check script for Icinga2 but you can use it with Nagios or other monitoring tool. I reserve the right to update it in the future, but feel free to fork it and create a better plugin.

# Prerequisites (on debian)
Install the NodeJS official repository for Debian and then:

    sudo apt install python-skimage/stable nodejs/stretch pillow imagemagick
    sudo npm install -g pageres-cli 
    sudo mkdir -p /var/spool/webping

# Configuration in Icinga
Configuration snippet:

    #####################################
    # Webpages   
    #####################################
    object CheckCommand "check_webpage" {
        command = [ "/opt/icinga2/webping/webping.py"]
        arguments = {
            "--website" = "$url$"
            "--warning" = "$warning$"
            "--critical" = "$critical$"
            "--area" = "$area$"
            "--baseweb" = "https://mon.eqs.range-id.web/webping/"
        }    
        timeout = 30s    
    }

    apply Service "WEBPAGE-" for (identifier => url in host.vars.webping.url) {
        import "range-service-slow-immediate"
        check_command = "check_webpage"
        vars.url = url.site
        vars.area = url.area
        vars.warning = "60"
        vars.critical = "100"
        assign where host.vars.webping.url
    }

    object Host "EQS-WEB-DEFACEMENT" {
        import "range-host"
        check_command = "dummy"
        address = "n.a."
        vars.webping.url["WWW-ANGELOXX-IT"] = {site = "www.angeloxx.it", area = "2,5,1272,263" }
    }