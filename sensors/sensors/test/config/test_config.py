import os
import unittest

from sensors.config.constants import *
from sensors.config import Config, ConfigurationError
from sensors.domain.sensor import Sensor
from sensors.domain.observed_property import ObservedProperty
from sensors.domain.transport import HttpsTransport


class TestConfiguration(unittest.TestCase):

    def test_config_one(self):
        os.environ[ENV_YAML_PATH] = '../data/config1.yml'
        c = Config(unittest=True).config

        # Simulator
        self.assertTrue(CFG_SIMULATOR in c)
        self.assertTrue(c[CFG_SIMULATOR])
        # Logging
        self.assertTrue(CFG_LOGGING_LOGGER_PATH in c)
        self.assertEqual(c[CFG_LOGGING_LOGGER_PATH], '/var/log/sensor.log')
        # Spooler
        self.assertTrue(CFG_SPOOLER_DB_PATH in c)
        self.assertEqual(c[CFG_SPOOLER_DB_PATH], '/var/spool/mqueue/sensor.sqlite')
        # Thing
        self.assertTrue(CFG_THING in c)
        t = c[CFG_THING]
        self.assertEqual(t.thing_id, '5474a427-f565-4233-8f82-a8178534b150')
        self.assertEqual(t.location_id, 'f5610fb9-1556-42d8-862c-1d290a9b5c58')
        # Sensors
        sensors = c[CFG_SENSORS]
        self.assertEqual(len(sensors), 2)
        # 1st sensor
        s = sensors[0]
        self.assertTrue(isinstance(s, Sensor))
        self.assertEqual(CFG_SENSOR_TYPE_MQ131, s.typ)
        ops = s.observed_properties
        self.assertEqual(len(ops), 1)
        # First (only) observed property
        o = ops[0]
        self.assertTrue(isinstance(o, ObservedProperty))
        self.assertEqual(o.name, 'ozone')
        self.assertEqual(o.datastream_id, '1af6b695-07c0-4024-aeb8-4ddf64dbf458')
        # 2nd sensor
        s = sensors[1]
        self.assertTrue(isinstance(s, Sensor))
        self.assertEqual(CFG_SENSOR_TYPE_DHT11, s.typ)
        ops = s.observed_properties
        self.assertEqual(len(ops), 2)
        # First observed property
        o = ops[0]
        self.assertTrue(isinstance(o, ObservedProperty))
        self.assertEqual(o.name, 'air_temperature')
        self.assertEqual(o.datastream_id, '1874209f-72b0-4d7f-993c-2707fa01ccd2')
        # Second observed property
        o = ops[1]
        self.assertTrue(isinstance(o, ObservedProperty))
        self.assertEqual(o.name, 'relative_humidity')
        self.assertEqual(o.datastream_id, 'ebb0cb98-f1ef-4bec-875f-f4775cd48bcd')
        # Transports
        transports = c[CFG_TRANSPORTS]
        self.assertEqual(len(transports), 1)
        t = transports[0]
        self.assertTrue(isinstance(t, HttpsTransport))
        self.assertEqual(CFG_TRANSPORT_TYPE_HTTPS, t.typ)
        self.assertEqual('https://myservice.com/auth', t.auth_url())
        self.assertEqual('https://myservice.com/v1.0/', t.url())
        self.assertEqual('6d770f60-9912-4545-9d3c-9e8dcf4a0dad', t.jwt_id())
        self.assertEqual('faac9ce4-fd2d-476b-9984-aee2b71dfc8e', t.jwt_key())

    def test_config_one_ro(self):
        os.environ[ENV_YAML_PATH] = '../data/config1_Ro.yml'
        c = Config(unittest=True).config

        # Simulator
        self.assertTrue(CFG_SIMULATOR in c)
        self.assertTrue(c[CFG_SIMULATOR])
        # Logging
        self.assertTrue(CFG_LOGGING_LOGGER_PATH in c)
        self.assertEqual(c[CFG_LOGGING_LOGGER_PATH], '/var/log/sensor.log')
        # Spooler
        self.assertTrue(CFG_SPOOLER_DB_PATH in c)
        self.assertEqual(c[CFG_SPOOLER_DB_PATH], '/var/spool/mqueue/sensor.sqlite')
        # Thing
        self.assertTrue(CFG_THING in c)
        t = c[CFG_THING]
        self.assertEqual(t.thing_id, '5474a427-f565-4233-8f82-a8178534b150')
        self.assertEqual(t.location_id, 'f5610fb9-1556-42d8-862c-1d290a9b5c58')
        # Sensors
        sensors = c[CFG_SENSORS]
        self.assertEqual(len(sensors), 2)
        # 1st sensor
        s = sensors[0]
        self.assertTrue(isinstance(s, Sensor))
        self.assertEqual(CFG_SENSOR_TYPE_MQ131, s.typ)
        ops = s.observed_properties
        self.assertEqual(len(ops), 1)
        # First (only) observed property
        o = ops[0]
        self.assertTrue(isinstance(o, ObservedProperty))
        self.assertEqual(o.name, 'ozone')
        self.assertEqual(o.datastream_id, '1af6b695-07c0-4024-aeb8-4ddf64dbf458')

    def test_config_one_dupe_ds_id(self):
        os.environ[ENV_YAML_PATH] = '../data/config1-dupe-ds_id.yml'
        with self.assertRaises(ConfigurationError):
            c = Config(unittest=True).config

    def test_config_one_dupe_transport(self):
        os.environ[ENV_YAML_PATH] = '../data/config1-dupe-transport.yml'
        with self.assertRaises(ConfigurationError):
            c = Config(unittest=True).config


if __name__ == '__main__':
    unittest.main()
