#!/usr/bin/env python

"""
@file inttest_ingest.py
@author Ian Katz <ijk5@mit.edu>
@test
"""

from twisted.trial import unittest
import ion.util.ionlog
from twisted.internet import defer

from iontest.iontest import ItvTestCase
from ion.core import ioninit

from ion.integration.ais.app_integration_service import AppIntegrationServiceClient


from ion.core.messaging.message_client import MessageClient
from ion.services.coi.datastore_bootstrap.ion_preload_config import MYOOICI_USER_ID

from ion.core.process.process import Process

from ion.integration.ais.ais_object_identifiers import AIS_RESPONSE_MSG_TYPE, \
                                                       AIS_REQUEST_MSG_TYPE, \
                                                       AIS_RESPONSE_ERROR_TYPE, \
                                                       VALIDATE_DATASOURCE_REQ

log = ion.util.ionlog.getLogger(__name__)
CONF = ioninit.config(__name__)

class IntTestAisValidateDataResource(ItvTestCase):

    app_dependencies = [
                # release file for r1
                ("res/deploy/r1deploy.rel", "id=1"),
                ]

    @defer.inlineCallbacks
    def setUp(self):
        yield self._start_container()

        proc  = Process()
        yield proc.spawn()

        self.aisc  = AppIntegrationServiceClient(proc=proc)
        self.mc    = MessageClient(proc=proc)

    @defer.inlineCallbacks
    def tearDown(self):
        yield self._stop_container()






    @defer.inlineCallbacks
    def test_validateDataResource_BadInput(self):
        """
        run through the validate code without proper input
        """

        log.info("Trying to call validateDataResource with the wrong GPB")
        validate_req_msg  = yield self.mc.create_instance(VALIDATE_DATASOURCE_REQ)
        result            = yield self.aisc.validateDataResource(validate_req_msg, MYOOICI_USER_ID)
        self.failUnlessEqual(result.MessageType, AIS_RESPONSE_ERROR_TYPE,
                             "validateDataResource accepted a GPB that was known to be the wrong type")

        log.info("Trying to call validateDataResource with an empty GPB")
        ais_req_msg = yield self.mc.create_instance(AIS_REQUEST_MSG_TYPE)
        validate_req_msg = ais_req_msg.CreateObject(VALIDATE_DATASOURCE_REQ)
        ais_req_msg.message_parameters_reference = validate_req_msg
        result_wrapped = yield self.aisc.validateDataResource(ais_req_msg, MYOOICI_USER_ID)
        self.failUnlessEqual(result_wrapped.MessageType, AIS_RESPONSE_ERROR_TYPE,
                             "validateDataResource accepted a GPB without a data_resource_url")




    @defer.inlineCallbacks
    def _validateDataResourcePositive(self, some_url):
        """
        @brief try to validate a sample data sources
        """
        r1 = yield self._validateDataResource(some_url)

        defer.returnValue(r1.dataResourceSummary)


    @defer.inlineCallbacks
    def test_validateDataResourcePositive_remote1(self):
        """
        @brief try to validate a sample data sources
        """

        res = yield self._validateDataResourcePositive("http://uop.whoi.edu/oceansites/ooi/OS_NTAS_2010_R_M-1.nc")

        self.failUnlessEqual(res.title, "Analysed foundation sea surface temperature, global")
        self.failUnlessEqual(res.references, "none")
        self.failUnlessEqual(res.source, "TMI-REMSS,AMSRE-REMSS,AQUA-MODIS-OPBG,TERRA-MODIS-OPBG")
        self.failUnlessEqual(res.institution, "Remote Sensing Systems")
        self.failUnlessEqual(res.ion_time_coverage_start, "2011-04-23 00:00:00 UTC")
        self.failUnlessEqual(res.ion_time_coverage_end, "2011-04-27 23:59:59 UTC")
        self.failUnlessEqual(res.ion_geospatial_lat_min, -89.956055)
        self.failUnlessEqual(res.ion_geospatial_lat_max, 89.956055)
        self.failUnlessEqual(res.ion_geospatial_lon_min, -179.95605)
        self.failUnlessEqual(res.ion_geospatial_lon_max, 179.95605)

    @defer.inlineCallbacks
    def test_validateDataResourcePositive_remote2(self):
        """
        @brief try to validate a sample data sources
        """
        res = yield self._validateDataResourcePositive("http://geoport.whoi.edu/thredds/dodsC/usgs/data0/rsignell/data/oceansites/OS_NTAS_2010_R_M-1.nc")

        self.failUnlessEqual(res.title, "NTAS 10 Real-time Mooring Data, System 1")
        #self.failUnlessEqual(res.references, "none")
        #self.failUnlessEqual(res.source, "TMI-REMSS,AMSRE-REMSS,AQUA-MODIS-OPBG,TERRA-MODIS-OPBG")
        #self.failUnlessEqual(res.institution, "Remote Sensing Systems")
        #self.failUnlessEqual(res.ion_time_coverage_start, "2011-04-23 00:00:00 UTC")
        #self.failUnlessEqual(res.ion_time_coverage_end, "2011-04-27 23:59:59 UTC")
        #self.failUnlessEqual(res.ion_geospatial_lat_min, -89.956055)
        #self.failUnlessEqual(res.ion_geospatial_lat_max, 89.956055)
        #self.failUnlessEqual(res.ion_geospatial_lon_min, -179.95605)
        #self.failUnlessEqual(res.ion_geospatial_lon_max, 179.95605)


    @defer.inlineCallbacks
    def test_validateDataResourcePositive_remote3(self):
        res = yield self._validateDataResourcePositive("http://hfrnet.ucsd.edu:8080/thredds/dodsC/HFRNet/USEGC/6km/hourly/RTV")

        self.failUnlessEqual(res.title, "Near-Real Time Surface Ocean Velocity")


    @defer.inlineCallbacks
    def test_validateDataResourcePositive_local1(self):
        res = yield self._validateDataResourcePositive("http://thredds.oceanobservatories.org/thredds/dodsC/cfcheckData/OS_WHOTS_2010_R_M-1.nc")
        self.failUnlessEqual(res.title, "WHOTS 7 near-real-time Mooring Data, System 1")

    @defer.inlineCallbacks
    def test_validateDataResourcePositive_local2(self):
        res = yield self._validateDataResourcePositive("http://thredds.oceanobservatories.org/thredds/dodsC/cfcheckData/OS_NTAS_2010_R_M-1.nc")
        self.failUnlessEqual(res.title, "NTAS 10 Real-time Mooring Data, System 1")

    @defer.inlineCallbacks
    def test_validateDataResourcePositive_local3(self):
        yield self._validateDataResourcePositive("http://thredds.oceanobservatories.org/thredds/dodsC/cfcheckData/bigbight.nc")
        #self.failUnlessEqual(res.title, "")

    @defer.inlineCallbacks
    def test_validateDataResourceNegative_remote1(self):

        yield self._validateDataResourceNegative("http://thredds1.pfeg.noaa.gov/thredds/dodsC/satellite/GR/ssta/1day")

    @defer.inlineCallbacks
    def test_validateDataResourceNegative_local1(self):

        yield self._validateDataResourceNegative("http://thredds.oceanobservatories.org/thredds/dodsC/cfcheckData/marcoora6km.nc")

    @defer.inlineCallbacks
    def test_validateDataResourceNegative_local2(self):

        yield self._validateDataResourceNegative("http://thredds.oceanobservatories.org/thredds/dodsC/cfcheckData/kokagg.nc")



    @defer.inlineCallbacks
    def _validateDataResourceNegative(self, url):

        log.info("Creating and wrapping validation request")
        ais_req_msg  = yield self.mc.create_instance(AIS_REQUEST_MSG_TYPE)
        validate_req_msg  = ais_req_msg.CreateObject(VALIDATE_DATASOURCE_REQ)
        ais_req_msg.message_parameters_reference = validate_req_msg


        validate_req_msg.data_resource_url = url
        result_wrapped = yield self.aisc.validateDataResource(ais_req_msg, MYOOICI_USER_ID)

        #skip the test if the problem is with the test system
        self._checkValidationService(validate_req_msg.data_resource_url, result_wrapped)

        self.failUnlessEqual(result_wrapped.MessageType, AIS_RESPONSE_ERROR_TYPE,
                             "validateDataResource passed a known-bad URL")

        self.failIfEqual(-1, result_wrapped.error_str.find(
                "AIS.ValidateDataResource.validate: INVALID: CF compliance failed x"),
                          "something must have gone wrong because although validation failed " +
                          "(as expected, known bad URL),  it wasn't based on errors found in the CF")


    @defer.inlineCallbacks
    def _validateDataResource(self, data_source_url):


        log.info("Creating and wrapping validation request")
        ais_req_msg  = yield self.mc.create_instance(AIS_REQUEST_MSG_TYPE)
        validate_req_msg  = ais_req_msg.CreateObject(VALIDATE_DATASOURCE_REQ)
        ais_req_msg.message_parameters_reference = validate_req_msg


        validate_req_msg.data_resource_url = data_source_url


        result_wrapped = yield self.aisc.validateDataResource(ais_req_msg, MYOOICI_USER_ID)

        #skip the test if the problem is with the test system
        self._checkValidationService(data_source_url, result_wrapped)

        #some extra infos
        extra = ""
        if result_wrapped.MessageType == AIS_RESPONSE_ERROR_TYPE:
            extra = ": " + result_wrapped.error_str

        self.failUnlessEqual(result_wrapped.MessageType, AIS_RESPONSE_MSG_TYPE,
                             "validateDataResource had an internal failure" + extra)

        self.failUnlessEqual(200, result_wrapped.result, "validateDataResource didn't return 200 OK")
        self.failUnlessEqual(1, len(result_wrapped.message_parameters_reference),
                             "validateDataResource returned a GPB with too many 'message_parameters_reference's")

        result = result_wrapped.message_parameters_reference[0]

        defer.returnValue(result)



    def _checkValidationService(self, url, response_msg):
        if response_msg.MessageType == AIS_RESPONSE_ERROR_TYPE:
            log.info("\n\n\n\n&&&&&&&&&&&&&&&&\n\n" + response_msg.error_str + "\n\n&&&&&&&&&&\n\n")

            refused = "Connection was refused by other side: 111: Connection refused. "
            bad_cdm = "Your system doesn't seem to have the CDM validation service configured properly"
            bad_cfc = "Your system doesn't seem to have the CF Checker configured properly"
            not_dap = "the dataset is not hosted on a DAP server and cannot be validated"
            innerex = ""
            extra   = ""

            # get some text for helpful messages
            tmp = "Inner exception: "
            pos = response_msg.error_str.find(tmp)
            if -1 < pos:
                endpos = response_msg.error_str.find(" :: ", pos + len(tmp))
                if -1 < endpos:
                    innerex = " (" + response_msg.error_str[pos + len(tmp):endpos] + ") "


            if -1 < response_msg.error_str.find(not_dap):
                raise unittest.SkipTest("Apparently " + not_dap + " (" + url + "). " + 
                                        "This could be due to a temporary server outage.")

            if -1 < response_msg.error_str.find("Could not perform CDM Validation.  " +
                                                "Please check the CDM Validator configuration."):
                if -1 < response_msg.error_str.find(refused):
                    raise unittest.SkipTest("Could not validate because connection was refused by " + url)
                else:
                    raise unittest.SkipTest(bad_cdm + innerex + " for " + url)

            if -1 < response_msg.error_str.find("Could not perform CF Validation.  " +
                                                "Please check the CF Checker configuration.  " +
                                                "Inner exception: validate_cf(): " +
                                                "Failed to spawn the cfchecks script."):
                raise unittest.SkipTest(bad_cfc + "; maybe cfchecks_binary is wrong")

            if -1 < response_msg.error_str.find("Could not perform CF Validation.  " +
                                                "Please check the CF Checker configuration."):
                raise unittest.SkipTest(bad_cfc)

            if -1 < response_msg.error_str.find("failure exitcode (1) during CF Validation.  " +
                                                "Please check the CF Checker configuration."):
                if response_msg.error_str.find("Could not read the UDUNITS2 xml database from:"):
                    extra = "; bad or missing location for UDUNITS2 xml database in cfchecks_args"
                raise unittest.SkipTest(bad_cfc + extra)

            if -1 < response_msg.error_str.find("failure exitcode (254) during CF Validation.  " +
                                                "Please check the CF Checker configuration."):
                #pass #apparently the 254 is a valid exit code and the warning message is misplaced
                raise unittest.SkipTest(bad_cfc + extra)


            if -1 < response_msg.error_str.find("COULD NOT OPEN FILE, PLEASE CHECK THAT NETCDF IS FORMATTED CORRECTLY."):
                raise unittest.SkipTest("provided url (" + url + ") doesn't appear to be properly accessible")

        log.info("\n\n\n\n&&&&&&&&&&&&&&&&\n\nTHAT WENT WELL I GUESS\n\n&&&&&&&&&&\n\n")

