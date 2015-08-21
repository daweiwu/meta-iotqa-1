'''Positively verify api sf_get_sensor_by_id'''
import os
from oeqa.utils.helper import get_files_dir
from oeqa.utils.ddt import ddt, file_data
from oeqa.oetest import oeRuntimeTest
@ddt
class TestGetSensorByID(oeRuntimeTest):
    '''Verify sensor can be returned by sensor id'''
    @file_data('sensor_id.json')
    def testGetSensorByID(self, value):
        '''Verify sensor can be returned by sensor id'''
        #Prepare test binaries to image        
        mkdir_path = "mkdir -p /opt/sensor-test/apps/"
        (status, output) = self.target.run(mkdir_path)
        copy_path = os.path.join(get_files_dir(), 'test_get_sensor_by_id')
        (status, output) = self.target.copy_to(copy_path, \
"/opt/sensor-test/apps/")
        #run test get sensor by id and show it's information
        client_cmd = "/opt/sensor-test/apps/test_get_sensor_by_id " \
                     + str(value)
        (status, output) = self.target.run(client_cmd)
        print output
        self.assertEqual(status, 1, msg="Error messages: %s" % output)
