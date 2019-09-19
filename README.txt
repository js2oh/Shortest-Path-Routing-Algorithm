CS456 Assignment3 README file

Name: Jun Sung Oh
Student ID: 20596770

Instructions to Run the Programs:
-To run the nse: ./nse-linux386 <routers_host> <nse_port>
-To run the routers: ./router
(In case I want to run the single router: ./router.sh <router_id> <nse_host> <nse_port> <router_port>)
-run nse and then router

-Parameters used:
	<routers_host>  -  the  host  where  the  routers  are  running (assume all routers running on the same host)
	<nse_port>  -  the  Network  State  Emulator  port  number

-Parameters used implicitly in router script:
	<router_id>  -  an  integer  that  represents  the  router  id (should be unique)
	<nse_host>  - the  host  where  the  Network  State  Emulator  is  running
	<nse_port> -  the  port  number  of  the  Network  State  Emulator
	<router_port> -  the  router  port

Undergrad Machines Tested on:
-nse-host: ubuntu1604-006
-router-host: ubuntu1604-008

Regarding Compilation:
-make: make version GNU Make 4.1
