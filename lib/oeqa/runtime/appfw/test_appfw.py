from oeqa.oetest import oeRuntimeTest
from oeqa.utils.decorators import tag
import time,json

class App(object):
    def __init__(self,target,name,manifest):
        self.target = target
        self.name = name
        self.manifest = manifest

    def getAppProcessInfo(self,keyword):
        ''' get info of process '''
        if len(keyword) > 8:
            keyword = keyword[:8]
        (status,output) = self.target.run(" ps axo pid,user:20,comm | grep -v grep | grep %s | head -n 1" % keyword)
        if 'invalid option' in output :
            (status,output) = self.target.run(" ps | grep -v grep | grep %s | head -n 1" % keyword)
            if status == 0 and output.strip():
                return output
            else:
                return None
        else:
            return output

    def getAppProcessID(self,keyword):
        ''' get PID of process '''
        info = self.getProcessInfo(keyword)
        if info:
            return info.split()[0]
        else:
            return None   
        
    def startApp(self):
        ''' start app '''
        (status,output) = self.target.run("systemctl start %s" % self.name)
        time.sleep(3)
        if status != 0 :
            return False
        (status,output) = self.target.run("machinectl -l")
        if status == 0 and self.name in output :
            pass
        else:
            return False
        PID = self.getProcessPID(self.name)
        if PID :
            return True 
        else:
            return False 
        
    def stopApp(self):
        ''' stop app '''
        PID = self.getProcessPID(self.name)
        if not PID:
            return False 
        (status,output) = self.target.run("systemctl stop %s" % self.name)
        time.sleep(3)
        if status != 0 :
            return False
        (status,output) = self.target.run("machinectl -l")
        if status == 0 and self.name not in output :
            pass
        else:
            return False
        PID = self.getProcessPID(self.name)
        if not PID:
            return True
        else:
            return False

    def getManifestJson(self):
        '''Parse manifest '''
        (status,output) = self.target.run("cat %s" % self.manifest)
        if 0 != status : 
            print 'No this manifest file:\n %s' % output)
            return None
        try:
            manifest_json = json.loads(output)
        except Exception,e :
            print '\nParse manifest failed,output is: \n %s ,\nError is : %s' % (output ,e)
            return None
        return manifest_json
        
    def isAutostart(self):
        '''Check app is autostart or not'''
        if self.getManifestJson():
            try:
                auto_start = manifest_json['autostart']
            except Exception,e :
                print 'No autostart section in manifest or parse manifest fail: %s' % e
                return False
        if 'yes' == auto_start :
           return True 
        else:
           return False
    def getAppInstallFolder(self):
        return os.path.join(self.name.split('-'))

    def getExtraEnvs(self):
        if self.getManifestJson():
            try:
                env_dict = manifest_json['environment']
                return env_dict
            except Exception,e :
                print 'No environment section in manifest or parse manifest fail: %s' % e
                return None

    def isInstalled(self):
       '''App is installed '''
        (status, output) = self.target.run("ls /apps/%s" % self.getAppInstallFolder())
        if 0 == status :
            return True
        else:
            print output
            return False
         
class AppFWTest(oeRuntimeTest):

    def setUp(self):
        node_app_name = 'iodine-nodetest'
        node_app_manifest = '/apps/iodine/nodetest/manifest'
        python_app_name = 'foodine-pythontest'
        python_app_manifest = '/apps/foodine/pythontest/manifest'
        appfwtest_app_name = 'appfwtest-commonapp'
        appfwtest_app_manifest = '/apps/appfwtest/commonapp/manifest'
        self.node_app = App(self.target, node_app_name, node_app_manifest)
        self.python_app = App(self.target, python_app_name, python_app_manifest)
        self.appfwtest_app = App(self.target, appfwtest_app_name, appfwtest_app_manifest)

    def _test_appFW_app_preinstall(self, app):
        '''check app is pre-installed'''
        self.assertTrue(app.isInstalled(),
                        "%s not integreated in image" % app.name)
        
    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_preinstall(self):
        '''check python app is pre-installed'''
        self._test_appFW_app_preinstall(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_preinstall(self):
        '''check python app is pre-installed'''
        self._test_appFW_app_preinstall(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def _test_appFW_app_start(self, app):
        ''' Check app start successfully '''
        self.assertTrue(app.startApp(),"fails to start app: %s" % app.name),

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_start(self):
        ''' Check node app start successfully '''
        self._test_appFW_app_start(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_start(self):
        ''' Check python app start successfully '''
        self._test_appFW_app_start(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_multi_app_start(self):
        ''' Check multi app start successfully '''
        self._test_appFW_app_start(self.node_app)
        self._test_appFW_app_start(self.python_app)

    @tag(TestType = 'FVT', FeattureID = 'IOTOS-337')
    def test_appFW_multi_app_stop(self):
        ''' Check multi app stop successfully '''
        self._test_appFW_app_stop(self.node_app)
        self._test_appFW_app_stop(self.python_app)

    @tag(TestType = 'FVT', FeattureID = 'IOTOS-337')
    def test_appFW_multi_app_start_stop(self):
        ''' Check multi app start/stop successfully '''
        self._test_appFW_app_start(self.node_app)
        self._test_appFW_app_stop(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def _test_appFW_app_stop(self, app):
        ''' Check app stop successfully '''
        self._test_appFW_app_start(app)
        self.assertTrue(app.stopApp(),"fals to stop app : %s" % app.name)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_stop(self):
        ''' Check node app stop successfully '''
        self._test_appFW_app_stop(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_stop(self):
        ''' Check python app stop successfully '''
        self._test_appFW_app_stop(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def _test_appFW_app_restart(self,app):
        ''' Check app restart successfully '''
        self._test_appFW_app_start(app)
        self._test_appFW_app_stop(app)
        self._test_appFW_app_start(app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_restart(self,app):
        ''' Check app restart successfully '''
        self._test_appFW_app_restart(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_restart(self,app):
        ''' Check python app restart successfully '''
        self._test_appFW_app_restart(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def _test_appFW_app_restop(self,app):
        ''' Check app restop successfully '''
        self._test_appFW_app_start(app)
        self._test_appFW_app_stop(app)
        self._test_appFW_app_start(app)
        self._test_appFW_app_stop(app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_restop(self,app):
        ''' Check node app restop successfully '''
        self._test_appFW_app_restop(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_restop(self,app):
        ''' Check python app restop successfully '''
        self._test_appFW_app_restop(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def _test_appFW_app_restart_systemctl(self, app):
        ''' Check app restart by systemctl restart successfully '''
        self._test_appFW_app_start(app)
        (status,output) = self.target.run("systemctl restart %s" % app.name)
        time.sleep(5)
        self.assertTrue(status == 0 , 'App restart by systemctl fail')
        self.assertTrue(app.getAppProcessID(),
                        'App restart by systemctl fail')
    
    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_node_app_restart_systemctl(self, app):
        ''' Check node app restart by systemctl restart successfully '''
        self._test_appFW_app_restart_systemctl(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-337')
    def test_appFW_python_app_restart_systemctl(self, app):
        ''' Check python app restart by systemctl restart successfully '''
        self._test_appFW_app_restart_systemctl(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-339')
    def _test_appFW_app_running_with_Dedicated_User(self, app):
        ''' check app launched by normal user '''
        self._test_appFW_app_start(app)
        p_info = app.getAppProcessInfo(app.name)
        self.assertTrue(p_info,'No see App running')
        p_name = p_info.split()[1]
        self.assertTrue(app.name[:8] == p_name , "Not found app running with dedicated user")
        # check the user is normal user by uid and gid
        (status,output) = self.target.run("id -u %s" % app.name)
        self.assertEqual(status, 0 , 'Fail to get uid : %s' % output)
        self.assertTrue(int(output)>=1000, 'Is not normal user, uid is: %s' % output)

        (status,output) = self.target.run("id -g %s" % app.name)
        self.assertEqual(status, 0 , 'Fail to get gid : %s' % output)
        self.assertTrue(int(output)>=1000, 'Is not normal user, uid is: %s' % output)
            
    @tag(TestType = 'FVT', FeatureID = 'IOTOS-339')
    def test_appFW_node_app_running_with_Dedicated_User(self, app):
        ''' check node app launched by normal user '''
        self._test_appFW_app_running_with_Dedicated_User(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-339')
    def test_appFW_python_app_running_with_Dedicated_User(self, app):
        ''' check python app launched by normal user '''
        self._test_appFW_app_running_with_Dedicated_User(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def _test_appFW_app_container_list(self, app):
        ''' check app listed in container '''
        self._test_appFW_app_start(app)
        (status,output) = self.target.run("machinectl -l")
        self.assertTrue(status == 0 and app.name in output , '%s : app not running in container' % output) 

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def test_appFW_node_app_container_list(self):
        ''' check node app listed in container '''
        self._test_appFW_app_container_list(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def test_appFW_python_app_container_list(self):
        ''' check python app listed in container '''
        self._test_appFW_app_container_list(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def _test_appFW_app_container_status(self, app):
        ''' check app status in container '''
        self._test_appFW_app_start(app)
        (status,output) = self.target.run("machinectl status %s" % app.name)
        self.assertTrue(status == 0 and app.name in output , '%s : app not running in container' % output) 
        (status,output) = self.target.run("machinectl show %s" % app.name)
        self.assertTrue(status == 0 and 'State=running' in output , '%s : app not running in container' % output) 
         
    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def test_appFW_app_container_status(self, app):
        ''' check node app status in container '''
        self._test_appFW_app_container_status(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-342')
    def test_appFW_app_container_status(self, app):
        ''' check python app status in container '''
        self._test_appFW_app_container_status(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-416')
    def _test_appFW_app_impersonation(self, app):
        ''' check access of app user accout '''
        self.assertTrue(app.isInstalled(),"app %s is not installed" % app.name)
        (status,output) = self.target.run("su %s" % app.name)
        self.assertTrue(status != 0 , 'Test access of app user account fail')

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-416')
    def _test_appFW_node_app_impersonation(self, app):
        ''' check access of node app user accout '''
        self._test_appFW_app_impersonation(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-416')
    def _test_appFW_python_app_impersonation(self, app):
        ''' check access of python app user accout '''
        self._test_appFW_app_impersonation(self.python_app)
             
    @tag(TestType = 'FVT', FeatureID = 'IOTOS-358')
    def test_appFW_sqlite_integrated(self):
        ''' Check sqlite is integrated in image'''
        (status,output) = self.target.run("ls /usr/lib/libsqlite*.so || ls /lib/libsqlite*.so")
        self.assertTrue(status == 0 , 'Check sqlite integration fail')

    def _test_appFW_app_autostart(self, app):
        ''' Check app is defined as autostart from manifest'''
        if app.isAutostart():
            self.assertTrue(app.getAppProcessID(),"app %s is not started at system startup" %s app.name)
        else:
            self.assertFalse(app.getAppProcessID(),"app %s is started at system startup" %s app.name)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-418')
    def test_appFW_node_app_autostart(self):
        ''' Check node app is defined as autostart from manifest'''
        self._test_appFW_app_autostart(self.node_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-418')
    def test_appFW_python_app_autostart(self):
        ''' Check python app is not defined as autostart from manifest'''
        self._test_appFW_app_autostart(self.python_app)

    @tag(TestType = 'FVT', FeatureID = 'IOTOS-418')
    def test_appFW_app_extra_envs(self):
        ''' Check app extra evns defined in manifest'''
        app = self.appfwtest_app
        self._test_appFW_app_start(app)
        envs = app.getExtraEnvs()
        self.assertTrue(envs, "Fail to get %s extra envs" % app.name)
        (status,output) = sefl.target.run("journalctl -ab")
        for k,v in envs.items():
            print k,v
            self.assertTrue( k + "=" + v in output, "Not found App extra envs"   
