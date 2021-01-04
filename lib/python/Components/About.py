from boxbranding import getImageVersion, getMachineBuild, getBoxType
from sys import modules
import socket, fcntl, struct, time, os

def getVersionString():
    return getImageVersion()


def getFlashDateString():
    try:
        f = open('/etc/install', 'r')
        flashdate = f.read()
        f.close()
        return flashdate
    except:
        return _('unknown')


def getEnigmaVersionString():
    return getImageVersion()


def getGStreamerVersionString():
    try:
        from glob import glob
        gst = [ x.split('Version: ') for x in open(glob('/var/lib/opkg/info/gstreamer[0-9].[0-9].control')[0], 'r') if x.startswith('Version:') ][0]
        return '%s' % gst[1].split('+')[0].replace('\n', '')
    except:
        return _('unknown')


def getKernelVersionString():
    try:
        f = open('/proc/version', 'r')
        kernelversion = f.read().split(' ', 4)[2].split('-', 2)[0]
        f.close()
        return kernelversion
    except:
        return _('unknown')


def getIsBroadcom():
    try:
        file = open('/proc/cpuinfo', 'r')
        lines = file.readlines()
        for x in lines:
            splitted = x.split(': ')
            if len(splitted) > 1:
                splitted[1] = splitted[1].replace('\n', '')
                if splitted[0].startswith('Hardware'):
                    system = splitted[1].split(' ')[0]
                elif splitted[0].startswith('system type'):
                    if splitted[1].split(' ')[0].startswith('BCM'):
                        system = 'Broadcom'

        file.close()
        if 'Broadcom' in system:
            return True
        return False
    except:
        return False


def getChipSetString():
    if getMachineBuild() in ('dm800',):
        return '7401'
    if getMachineBuild() in ('dm800se',):
        return '7405'
    if getMachineBuild() in ('dm7080', 'dm820'):
        return '7435'
    if getMachineBuild() in ('dm520', 'dm525'):
        return '73625'
    if getMachineBuild() in ('dm900', 'dm920', 'et13000', 'sf5008'):
        return '7252S'
    if getMachineBuild() in ('hd51', 'vs1500', 'h7'):
        return '7251S'
    if getMachineBuild() in ('alien5',):
        return 'S905D'
    try:
        f = open('/proc/stb/info/chipset', 'r')
        chipset = f.read()
        f.close()
        return str(chipset.lower().replace('\n', '').replace('bcm', '').replace('brcm', '').replace('sti', ''))
    except IOError:
        return 'unavailable'


def getCPUSpeedMHzInt():
    cpu_speed = 0
    try:
        file = open('/proc/cpuinfo', 'r')
        lines = file.readlines()
        file.close()
        for x in lines:
            splitted = x.split(': ')
            if len(splitted) > 1:
                splitted[1] = splitted[1].replace('\n', '')
                if splitted[0].startswith('cpu MHz'):
                    cpu_speed = float(splitted[1].split(' ')[0])
                    break

    except IOError:
        print '[About] getCPUSpeedMHzInt, /proc/cpuinfo not available'

    if cpu_speed == 0:
        if getMachineBuild() in ('h7', 'hd51', 'hd52', 'sf4008'):
            try:
                import binascii
                f = open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb')
                clockfrequency = f.read()
                f.close()
                cpu_speed = round(int(binascii.hexlify(clockfrequency), 16) / 1000000, 1)
            except IOError:
                cpu_speed = 1700

        else:
            try:
                file = open('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq', 'r')
                cpu_speed = float(file.read()) / 1000
                file.close()
            except IOError:
                print '[About] getCPUSpeedMHzInt, /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq not available'

    return int(cpu_speed)


def getCPUSpeedString():
    if getMachineBuild() in ('dm800',):
        return '295 MHz'
    if getMachineBuild() in ('dm800se',):
        return '405 MHz'
    if getMachineBuild() in ('u41', 'u42', 'u43'):
        return '1.0 GHz'
    if getMachineBuild() in ('dags72604', 'vusolo4k', 'vuultimo4k', 'vuzero4k'):
        return '1.5 GHz'
    if getMachineBuild() in ('formuler1tc', 'formuler1', 'triplex', 'tiviaraplus'):
        return '1.3 GHz'
    if getMachineBuild() in ('gbmv200', 'u51', 'u52', 'u53', 'u532', 'u533', 'u54', 'u55', 'u56', 'u5', 'u5pvr', 'h9', 'h9combo', 'h10', 'cc1', 'sf8008', 'hd60', 'hd61', 'i55plus', 'ustym4kpro', 'beyonwizv2', 'viper4k', 'v8plus', 'multibox'):
        return '1.6 GHz'
    if getMachineBuild() in ('vuuno4kse', 'vuuno4k', 'dm900', 'dm920', 'gb7252', 'dags7252', 'xc7439', '8100s'):
        return '1.7 GHz'
    if getMachineBuild() in ('alien5',):
        return '2.0 GHz'
    if getMachineBuild() in ('vuduo4k',):
        return '2.1 GHz'
    if getMachineBuild() in ('hd51', 'hd52', 'sf4008', 'vs1500', 'et1x000', 'h7', 'et13000', 'sf5008', 'osmio4k', 'osmio4kplus', 'osmini4k'):
        try:
            import binascii
            f = open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb')
            clockfrequency = f.read()
            f.close()
            return '%s MHz' % str(round(int(binascii.hexlify(clockfrequency), 16) / 1000000, 1))
        except:
            return '1.7 GHz'

    else:
        try:
            file = open('/proc/cpuinfo', 'r')
            lines = file.readlines()
            for x in lines:
                splitted = x.split(': ')
                if len(splitted) > 1:
                    splitted[1] = splitted[1].replace('\n', '')
                    if splitted[0].startswith('cpu MHz'):
                        mhz = float(splitted[1].split(' ')[0])
                        if mhz and mhz >= 1000:
                            mhz = '%s GHz' % str(round(mhz / 1000, 1))
                        else:
                            mhz = '%s MHz' % str(round(mhz, 1))

            file.close()
            return mhz
        except IOError:
            return 'unavailable'


def getCPUArch():
    if 'ARM' in getCPUString():
        return getCPUString()
    return _('Mipsel')


def getCPUString():
    system = _('unavailable')
    try:
        file = open('/proc/cpuinfo', 'r')
        lines = file.readlines()
        for x in lines:
            splitted = x.split(': ')
            if len(splitted) > 1:
                splitted[1] = splitted[1].replace('\n', '')
                if splitted[0].startswith('system type'):
                    system = splitted[1].split(' ')[0]
                elif splitted[0].startswith('model name'):
                    system = splitted[1].split(' ')[0]
                elif splitted[0].startswith('Processor'):
                    system = splitted[1].split(' ')[0]

        file.close()
        return system
    except IOError:
        return _('unavailable')


def getCpuCoresInt():
    cores = 0
    try:
        file = open('/proc/cpuinfo', 'r')
        lines = file.readlines()
        file.close()
        for x in lines:
            splitted = x.split(': ')
            if len(splitted) > 1:
                splitted[1] = splitted[1].replace('\n', '')
                if splitted[0].startswith('processor'):
                    cores = int(splitted[1]) + 1

    except IOError:
        pass

    return cores


def getCpuCoresString():
    cores = getCpuCoresInt()
    return {0: _('unavailable'),
     1: _('Single core'),
     2: _('Dual core'),
     4: _('Quad core'),
     8: _('Octo core')}.get(cores, _('%d cores') % cores)


def _ifinfo(sock, addr, ifname):
    iface = struct.pack('256s', ifname[:15])
    info = fcntl.ioctl(sock.fileno(), addr, iface)
    if addr == 35111:
        return ''.join([ '%02x:' % ord(char) for char in info[18:24] ])[:-1].upper()
    else:
        return socket.inet_ntoa(info[20:24])


def getIfConfig(ifname):
    ifreq = {'ifname': ifname}
    infos = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    infos['addr'] = 35093
    infos['brdaddr'] = 35097
    infos['hwaddr'] = 35111
    infos['netmask'] = 35099
    try:
        for k, v in infos.items():
            ifreq[k] = _ifinfo(sock, v, ifname)

    except:
        pass

    sock.close()
    return ifreq


def getIfTransferredData(ifname):
    f = open('/proc/net/dev', 'r')
    for line in f:
        if ifname in line:
            data = line.split('%s:' % ifname)[1].split()
            rx_bytes, tx_bytes = data[0], data[8]
            f.close()
            return (rx_bytes, tx_bytes)


def getPythonVersionString():
    import sys
    return '%s.%s.%s' % (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def getFFmpegVersionString():
	try:
		from glob import glob
		ffmpeg = [x.split("Version: ") for x in open(glob("/var/lib/opkg/info/ffmpeg.control")[0], "r") if x.startswith("Version:")][0]
		version = ffmpeg[1].split("-")[0].replace("\n","")
		return "%s" % version.split("+")[0]
	except:
		return ""


about = modules[__name__]
