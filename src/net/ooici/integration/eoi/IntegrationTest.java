/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package net.ooici.integration.eoi;

import ion.core.messaging.IonMessage;
import ion.core.messaging.MessagingName;
import ion.core.messaging.MsgBrokerClient;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.HashMap;
import junit.framework.TestCase;
import net.ooici.eoi.netcdf.NcUtils;
import net.ooici.eoi.proto.Unidata2Ooi;
import ooici.netcdf.iosp.OOICIiosp;
import ooici.netcdf.iosp.IospUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import ucar.nc2.dataset.NetcdfDataset;

/**
 *
 * @author cmueller
 */
public class IntegrationTest {

    private static Logger log = LoggerFactory.getLogger(IntegrationTest.class);

    public IntegrationTest() {
        MsgBrokerClient cli = null;
        NetcdfDataset ncds_out = null;
        NetcdfDataset ncds_back = null;
        int retInt = 1;
        try {
            /* Get the test dataset */
            ncds_out = NetcdfDataset.openDataset("test_data/USGS_Test.nc");

            /* Serialize the dataset for transport */
            byte[] bytes_out = Unidata2Ooi.ncdfToByteArray(ncds_out);

            /* Create the broker to send/receive the data */
            java.util.HashMap<String, String> connInfo = IospUtils.parseProperties(new java.io.File("ooici-conn.properties"));
            MessagingName toName = new MessagingName(connInfo.get("exchange"), connInfo.get("service"));
            cli = new MsgBrokerClient(connInfo.get("server"), com.rabbitmq.client.AMQP.PROTOCOL.PORT, connInfo.get("topic"));
            MessagingName fromName = ion.core.messaging.MessagingName.generateUniqueName();
            cli.attach();
            String recieverQueue = cli.declareQueue(null);
            cli.bindQueue(recieverQueue, fromName, null);
            cli.attachConsumer(recieverQueue);

            /* Send the data to the eoi_ingest service */
            IonMessage dataMessage = cli.createMessage(fromName, toName, "ingest", bytes_out);
            dataMessage.getIonHeaders().put("encoding", "ION R1 GPB");
            cli.sendMessage(dataMessage);
            IonMessage reply = cli.consumeMessage(recieverQueue);
            String resID = reply.getContent().toString();

            System.out.println(">>>> Returned OOI Resource ID: " + resID);

            /* Register the OOICI IOSP */
            OOICIiosp.init(connInfo);
            NetcdfDataset.registerIOProvider(OOICIiosp.class);
            /* Retrieve the data and regenerate it */
            ncds_back = NetcdfDataset.openDataset("ooici:" + resID);

            retInt = (NcUtils.checkEqual(ncds_out, ncds_back)) ? 0 : 1;
            
            System.out.println("Datasets equal == " + ((retInt == 0) ? "true" : "false"));

        } catch (IllegalAccessException ex) {
            log.error("Error performing integration test", ex);
        } catch (InstantiationException ex) {
            log.error("Error performing integration test", ex);
        } catch (IOException ex) {
            log.error("Error performing integration test", ex);
        } finally {
            /* Dispose of the broker */
            if (cli != null) {
                cli.detach();
                cli = null;
            }
            try {
                /* Close the NetcdfDataset objects - must call "close" to dispose of the internal broker connection*/
                if (ncds_out != null) {
                    ncds_out.close();
                }
                if (ncds_back != null) {
                    ncds_back.close();
                }
            } catch (IOException ex) {
                log.error("Error closing datasets", ex);
            }
        }
        
        System.exit(retInt);
    }

    public static void main(String[] args) {
        new IntegrationTest();
    }

}
