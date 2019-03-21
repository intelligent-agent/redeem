import unittest
import mock    # use mock.Mock etc
import sys

sys.modules['evdev'] = mock.Mock()
sys.modules['redeem.PWM'] = mock.Mock()

from redeem.Stepper_TMC2130 import Stepper_TMC2130, StepperBankSpi


class TestTMC2130_SingleStepper(unittest.TestCase):
  def setUp(self):
    self.spi = mock.Mock()
    self.bank = StepperBankSpi(self.spi, 1)
    self.stepper = Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "X", self.bank, 0)

  def test_gconf_bit_sanity(self):
    self.stepper.gconf.data.register = 0x00000002

    # check the lowest four bits
    self.assertEqual(self.stepper.gconf.data.bits.i_scale_analog, 0)
    self.assertEqual(self.stepper.gconf.data.bits.internal_rsense, 1)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.gconf.data.bits.enc_commutation, 0)

  def test_status_bit_sanity(self):
    self.stepper.update_status(0x5)

    self.assertEqual(self.stepper.status.bits.standstill, 0)
    self.assertEqual(self.stepper.status.bits.sg2, 1)
    self.assertEqual(self.stepper.status.bits.driver_error, 0)
    self.assertEqual(self.stepper.status.bits.reset_flag, 1)

  def test_single_register_read(self):
    self.spi.xfer = mock.Mock(side_effect=[[0xff] * 5, [0xff, 0xab, 0xcd, 0xef, 0x12]])

    self.stepper._read_register(self.stepper.gconf)

    self.spi.xfer.assert_has_calls([mock.call([0] * 5), mock.call([0] * 5)])
    self.assertEqual(self.stepper.gconf.data.register, 0xabcdef12)

  def test_single_register_write(self):
    self.spi.xfer = mock.Mock(side_effect=[[0] * 5])

    self.stepper.gconf.data.register = 0xabcdef12
    self.stepper._write_register(self.stepper.gconf)

    self.spi.xfer.assert_has_calls([mock.call([0x80, 0xab, 0xcd, 0xef, 0x12])])
    self.assertEqual(self.stepper.gconf.data.register,
                     0xabcdef12)    # the register value shouldn't have changed

  def test_status_update_on_read(self):
    self.spi.xfer = mock.Mock(side_effect=[[0xff] * 5, [0xf, 0xab, 0xcd, 0xef, 0x12]])

    self.stepper._read_register(self.stepper.gconf)

    self.assertEqual(self.stepper.get_status(), 0xf)

  def test_status_update_on_write(self):
    self.spi.xfer = mock.Mock(side_effect=[[0xf, 0, 0, 0, 0]])

    self.stepper._write_register(self.stepper.gconf)

    self.assertEqual(self.stepper.get_status(), 0xf)

  def test_microstepping_settings(self):
    self.spi.xfer = mock.Mock(return_value=[0] * 5)

    self.stepper.set_microstepping(0)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)    # no stealthchop
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 0)    # no interpolation
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 8)    # whole steps

    self.stepper.set_microstepping(1)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 7)

    self.stepper.set_microstepping(2)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 7)

    self.stepper.set_microstepping(3)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 6)

    self.stepper.set_microstepping(4)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 4)

    self.stepper.set_microstepping(5)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 6)

    self.stepper.set_microstepping(6)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 0)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 4)

    self.stepper.set_microstepping(7)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 6)

    self.stepper.set_microstepping(8)
    self.assertEqual(self.stepper.gconf.data.bits.en_pwm_mode, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.intpol, 1)
    self.assertEqual(self.stepper.chopconf.data.bits.mres, 4)

  def test_writes_registers_on_microstepping_update(self):
    self.spi.xfer = mock.Mock(side_effect=[[0] * 5, [0] * 5])

    self.stepper.set_microstepping(8)

    self.spi.xfer.assert_has_calls([
    # chopconf has mres=4, intpol=1
        mock.call([0x80 | 0x6C, 0x14, 0x0, 0x0, 0x0]),
    # gconf has en_pwm_mode
        mock.call([0x80, 0x0, 0x0, 0x0, 0x4]),
    ])

  def test_enable(self):
    self.spi.xfer = mock.Mock(return_value=[0] * 5)

    # this is emulating initialize_registers
    self.stepper.chopconf.data.bits.toff = 4

    self.stepper.set_enabled()
    self.spi.xfer.assert_called_once_with([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x04])

  def test_disable(self):
    self.spi.xfer = mock.Mock(return_value=[0] * 5)

    # this is emulating initialize_registers
    self.stepper.chopconf.data.bits.toff = 4

    self.stepper.set_enabled()
    self.stepper.set_disabled()
    self.spi.xfer.assert_has_calls([
        mock.call([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x04]),
        mock.call([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x0])
    ])

  def test_reset(self):
    self.spi.xfer = mock.Mock(return_value=[0] * 5)

    # this is emulating initialize_registers
    self.stepper.chopconf.data.bits.toff = 4

    self.stepper.set_enabled()

    self.stepper.reset()
    self.spi.xfer.assert_has_calls([
        mock.call([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x04]),
        mock.call([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x0]),
        mock.call([0x80 | 0x6C, 0x0, 0x0, 0x0, 0x04])
    ])

  def test_initialize_register(self):
    self.spi.xfer = mock.Mock(return_value=[0] * 5)

    self.stepper.initialize_registers()

    self.spi.xfer.assert_has_calls([
    # tpowerdown is 10
        mock.call([0x80 | 0x11, 0x0, 0x0, 0x0, 0xa]),
    # gconf has diag0_error, diag0_otpw, diag0_stall, diag1_stall
        mock.call([0x80 | 0x00, 0x0, 0x0, 0x01, 0xE0]),
    # chopconf has vsense, tbl=2, hstrt=4, hend=1
        mock.call([0x80 | 0x6C, 0x00, 0x03, 0x0, 0xC0]),
    # ihold_irun has ihold_delay = 10
        mock.call([0x80 | 0x10, 0x0, 0xa, 0x0, 0x0]),
    # pwmconf has pwm_ampl=200, pwm_grad=1, pwm_autoscale
        mock.call([0x80 | 0x70, 0x0, 0x4, 0x1, 0xC8]),
    # read gstat - once for show
        mock.call([0x1, 0x0, 0x0, 0x0, 0x0]),
    # and once for real
        mock.call([0x1, 0x0, 0x0, 0x0, 0x0])
    ])


class TestTMC2130_SparseTwoStepper(unittest.TestCase):
  def setUp(self):
    self.spi = mock.Mock()
    self.bank = StepperBankSpi(self.spi, 2)
    self.stepper = Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "X", self.bank, 1)

  def test_double_stepper_bank_single_register_read(self):
    self.spi.xfer = mock.Mock(
        side_effect=[[0] * (5 * 6), [0, 0x22, 0x22, 0x22, 0x22, 0, 0x11, 0x11, 0x11, 0x11]])

    self.stepper._read_register(self.stepper.gconf)

    self.spi.xfer.assert_has_calls([mock.call([0] * 10), mock.call([0] * 10)])

  def test_double_stepper_bank_single_register_write(self):
    self.spi.xfer = mock.Mock(side_effect=[[0] * 10])

    self.stepper.gconf.data.register = 0x22222222
    self.stepper._write_register(self.stepper.gconf)

    self.spi.xfer.assert_called_once_with([0x80, 0x22, 0x22, 0x22, 0x22] + [0] * 5)
    self.assertEqual(self.stepper.gconf.data.register, 0x22222222)

  def test_status_update_on_read(self):
    self.spi.xfer = mock.Mock(
        side_effect=[[0] * (5 * 2), [0xa, 0x22, 0x22, 0x22, 0x22, 0x5, 0x11, 0x11, 0x11, 0x11]])

    self.stepper._read_register(self.stepper.gconf)

    self.assertEqual(self.stepper.get_status(), 0xa)
    self.spi.xfer.assert_has_calls([mock.call([0] * 10), mock.call([0] * 10)])

  def test_status_update_on_write(self):
    self.spi.xfer = mock.Mock(side_effect=[[0x5] + [0] * 4 + [0xa] + [0] * 4])

    self.stepper.gconf.data.register = 0x22222222
    self.stepper._write_register(self.stepper.gconf)

    self.assertEqual(self.stepper.get_status(), 0x5)


class TestTMC2130_SparseSixStepper(unittest.TestCase):
  def setUp(self):
    self.spi = mock.Mock()
    self.bank = StepperBankSpi(self.spi, 6)
    self.steppers = [
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "X", self.bank, 0),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "Y", self.bank, 1),
        None,
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "E", self.bank, 3),
        None,
        None,
    ]

  def test_single_register_read(self):
    spi_return = [0] + [0x66] * 4 + [0] + [0x55] * 4 + [0] + [0x44] * 4 + [0] + [0x33] * 4 + [
        0
    ] + [0x22] * 4 + [0] + [0x11] * 4
    self.spi.xfer = mock.Mock(side_effect=[[0] * (6 * 5), spi_return])

    self.steppers[3]._read_register(self.steppers[3].gconf)

    self.spi.xfer.assert_has_calls([mock.call([0] * 5 * 6), mock.call([0] * 5 * 6)])
    self.assertEqual(self.steppers[3].gconf.data.register, 0x44444444)

  def test_bulk_register_read(self):
    spi_return = [0] + [0x66] * 4 + [0] + [0x55] * 4 + [0] + [0x44] * 4 + [0] + [0x33] * 4 + [
        0
    ] + [0x22] * 4 + [0] + [0x11] * 4
    self.spi.xfer = mock.Mock(side_effect=[[0] * (5 * 6), spi_return])

    self.bank.read_all_registers(self.steppers[0].gconf.addr)

    self.spi.xfer.assert_has_calls([mock.call([0] * 5 * 6), mock.call([0] * 5 * 6)])
    self.assertEqual(self.steppers[0].gconf.data.register, 0x11111111)
    self.assertEqual(self.steppers[1].gconf.data.register, 0x22222222)
    self.assertEqual(self.steppers[3].gconf.data.register, 0x44444444)

  def test_single_register_write(self):
    spi_return = [0] * (5 * 6)
    self.spi.xfer = mock.Mock(side_effect=[spi_return])

    self.steppers[3].gconf.data.register = 0x44444444
    self.steppers[3]._write_register(self.steppers[3].gconf)

    self.spi.xfer.assert_called_once_with([0] * (5 * 2) + [0x80, 0x44, 0x44, 0x44, 0x44] +
                                          [0] * (5 * 3))
    self.assertEqual(self.steppers[3].gconf.data.register, 0x44444444)

  def test_bulk_register_write(self):
    spi_return = [0] * (5 * 6)
    self.spi.xfer = mock.Mock(side_effect=[spi_return])

    self.steppers[0].gconf.data.register = 0x11111111
    self.steppers[1].gconf.data.register = 0x22222222
    self.steppers[3].gconf.data.register = 0x44444444
    self.bank.write_all_registers(self.steppers[0].gconf.addr)

    self.spi.xfer.assert_called_once_with([0] * (5 * 2) + [0x80, 0x44, 0x44, 0x44, 0x44] + [0] * 5 +
                                          [0x80, 0x22, 0x22, 0x22, 0x22] +
                                          [0x80, 0x11, 0x11, 0x11, 0x11])
    self.assertEqual(self.steppers[0].gconf.data.register, 0x11111111)
    self.assertEqual(self.steppers[1].gconf.data.register, 0x22222222)
    self.assertEqual(self.steppers[3].gconf.data.register, 0x44444444)

  def test_status_update_on_bulk_read(self):
    spi_return = [0x6] + [0x66] * 4 + [0x5] + [0x55] * 4 + [0x4] + [0x44] * 4 + [
        0x3
    ] + [0x33] * 4 + [0x2] + [0x22] * 4 + [0x1] + [0x11] * 4
    self.spi.xfer = mock.Mock(side_effect=[[0] * (5 * 6), spi_return])

    self.bank.read_all_registers(self.steppers[0].gconf.addr)

    self.assertEqual(self.steppers[0].get_status(), 0x1)
    self.assertEqual(self.steppers[1].get_status(), 0x2)
    self.assertEqual(self.steppers[3].get_status(), 0x4)

  def test_status_update_on_bulk_write(self):
    spi_return = [0] * (5 * 2) + [0x4] + [0] * 4 + [0] * 5 + [0x2] + [0] * 4 + [0x1] + [0] * 4
    self.spi.xfer = mock.Mock(side_effect=[spi_return])

    self.steppers[0].gconf.data.register = 0x11111111
    self.steppers[1].gconf.data.register = 0x22222222
    self.steppers[3].gconf.data.register = 0x44444444
    self.bank.write_all_registers(self.steppers[0].gconf.addr)

    self.assertEqual(self.steppers[0].get_status(), 0x1)
    self.assertEqual(self.steppers[1].get_status(), 0x2)
    self.assertEqual(self.steppers[3].get_status(), 0x4)


class TestTMC2130_SixStepper(unittest.TestCase):
  def setUp(self):
    self.spi = mock.Mock()
    self.bank = StepperBankSpi(self.spi, 6)
    self.steppers = [
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "X", self.bank, 0),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "Y", self.bank, 1),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "Z", self.bank, 2),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "E", self.bank, 3),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "H", self.bank, 4),
        Stepper_TMC2130(mock.Mock(), mock.Mock(), mock.Mock(), "A", self.bank, 5),
    ]

  def test_bulk_register_read(self):
    spi_return = [0] + [0x66] * 4 + [0] + [0x55] * 4 + [0] + [0x44] * 4 + [0] + [0x33] * 4 + [
        0
    ] + [0x22] * 4 + [0] + [0x11] * 4
    self.spi.xfer = mock.Mock(side_effect=[[0] * (5 * 6), spi_return])

    self.bank.read_all_registers(self.steppers[0].gconf.addr)

    self.spi.xfer.assert_has_calls([mock.call([0] * 5 * 6), mock.call([0] * 5 * 6)])

    for index, stepper in enumerate(self.steppers):
      self.assertEqual(stepper.gconf.data.register, (index + 1) * 0x11111111)

  def test_bulk_register_write(self):
    spi_return = [0] * (5 * 6)
    self.spi.xfer = mock.Mock(side_effect=[spi_return])

    for index, stepper in enumerate(self.steppers):
      stepper.gconf.data.register = (index + 1) * 0x11111111

    self.bank.write_all_registers(self.steppers[0].gconf.addr)

    self.spi.xfer.assert_called_once_with([0x80] + [0x66] * 4 + [0x80] + [0x55] * 4 + [0x80] +
                                          [0x44] * 4 + [0x80] + [0x33] * 4 + [0x80] + [0x22] * 4 +
                                          [0x80] + [0x11] * 4)

    for index, stepper in enumerate(self.steppers):
      self.assertEqual(stepper.gconf.data.register, (index + 1) * 0x11111111)

  def test_status_update_on_bulk_register_read(self):
    spi_return = [0x66] * 5 + [0x55] * 5 + [0x44] * 5 + [0x33] * 5 + [0x22] * 5 + [0x11] * 5
    self.spi.xfer = mock.Mock(side_effect=[[0] * (5 * 6), spi_return])

    self.bank.read_all_registers(self.steppers[0].gconf.addr)

    for index, stepper in enumerate(self.steppers):
      # the top byte is masked out
      self.assertEqual(stepper.get_status(), (index + 1))

  def test_status_update_on_bulk_register_write(self):
    spi_return = [0x66] * 5 + [0x55] * 5 + [0x44] * 5 + [0x33] * 5 + [0x22] * 5 + [0x11] * 5
    self.spi.xfer = mock.Mock(side_effect=[spi_return])

    for index, stepper in enumerate(self.steppers):
      stepper.gconf.data.register = (index + 1) * 0x11111111

    self.bank.write_all_registers(self.steppers[0].gconf.addr)

    for index, stepper in enumerate(self.steppers):
      # the top byte is masked out
      self.assertEqual(stepper.get_status(), index + 1)
