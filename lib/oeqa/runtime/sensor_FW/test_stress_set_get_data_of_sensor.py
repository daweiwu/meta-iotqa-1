'''Verify can repeatly set and get data on target sensor'''
import os
from oeqa.utils.helper import get_files_dir
from oeqa.oetest import oeRuntimeTest
from oeqa.utils.ddt import ddt, file_data

@ddt
class TestStreeSetGetDataOfSensor(oeRuntimeTest):
    '''Verify can set and get data on sensor for 100 times'''
    @file_data('sensor_id.json')
    def testStreeSetGetDataOfSensor(self, value):
        '''Verify can set and get data on sensor for 100 times'''
        mkdir_path = "mkdir -p /opt/sensor-test/apps"
        (status, output) = self.target.run(mkdir_path)
        copy_to_path = os.path.join(get_files_dir(), 'test_stress_set_get_data_of_sensor')
        (status, output) = self.target.copy_to(copy_to_path, \
"/opt/sensor-test/apps/")
        #run test stress set get data of sensor and show it's information
        client_cmd = "/opt/sensor-test/apps/test_stress_set_get_data_of_sensor " \
                     + str(value)
        (status, output) = self.target.run(client_cmd)
        print output
        self.assertEqual(status, 1, msg="Error messages: %s" % output)
