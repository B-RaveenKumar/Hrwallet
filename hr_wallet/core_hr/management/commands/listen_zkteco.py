import time
import signal
import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from core_hr.models import BiometricDevice
from profile_api.views import _process_event  # reuse ingestion logic

logger = logging.getLogger(__name__)

try:
    # python-zk (ZKTeco SDK wrapper)
    from zk import ZK, const
    HAS_ZK = True
except Exception:
    ZK = None
    const = None
    HAS_ZK = False


class Command(BaseCommand):
    help = "Open a live connection to a ZKTeco device and stream attendance events in real-time."

    def add_arguments(self, parser):
        parser.add_argument('--device-id', type=int, help='BiometricDevice ID to connect to (recommended)')
        parser.add_argument('--ip', type=str, help='Device IP (overrides device record if provided)')
        parser.add_argument('--port', type=int, default=4370, help='Device port (default 4370)')
        parser.add_argument('--reconnect-seconds', type=int, default=10, help='Backoff before reconnect on failure')
        parser.add_argument('--deactivation-timeout', type=int, default=60, help='Seconds before device is marked inactive if not seen')

    def handle(self, *args, **options):
        if not HAS_ZK:
            raise CommandError('python-zk not installed. Install with `pip install zk`.')

        device = None
        if options.get('device_id'):
            try:
                device = BiometricDevice.objects.get(pk=options['device_id'])
            except BiometricDevice.DoesNotExist:
                raise CommandError(f"Device id {options['device_id']} not found")
        if device is None and not options.get('ip'):
            raise CommandError('Provide --device-id or --ip to connect.')

        ip = options.get('ip') or (device.ip_address if device else None)
        port = options.get('port') or (device.port if device else 4370)
        if not ip:
            raise CommandError('No IP address specified or configured on device record.')
        # If connecting by IP only, try to resolve device to get comm_key before connecting
        if device is None:
            device = BiometricDevice.objects.filter(ip_address=ip).first()

        self.stdout.write(self.style.SUCCESS(f"Starting live capture for {ip}:{port} (device_id={getattr(device, 'id', None)})"))

        interrupted = False
        last_seen_time = None
        deactivation_timeout = int(options.get('deactivation_timeout') or 60)

        def _sigint(sig, frame):
            nonlocal interrupted
            interrupted = True
            self.stdout.write('Stopping...')

        signal.signal(signal.SIGINT, _sigint)

        while not interrupted:
            try:
                try:
                    password = int(getattr(device, 'comm_key', 0) or 0)
                    zk = ZK(ip, port=port, timeout=10, password=password, force_udp=False, ommit_ping=False)
                    conn = zk.connect()
                except Exception:
                    self.stdout.write(self.style.WARNING('TCP connect failed; retrying with UDP...'))
                    password = int(getattr(device, 'comm_key', 0) or 0)
                    zk = ZK(ip, port=port, timeout=10, password=password, force_udp=True, ommit_ping=False)
                    conn = zk.connect()
                self.stdout.write(self.style.SUCCESS('Connected. Listening for live events... (Ctrl+C to stop)'))
                # Mark device as active on successful connection
                if device:
                    device.is_active = True
                    device.last_seen = timezone.now()
                    device.save(update_fields=['is_active', 'last_seen'])
                    last_seen_time = time.time()
                try:
                    # On some devices, you may need to enable real-time events
                    try:
                        conn.disable_device()  # prevent device UI interference
                        conn.enable_device()   # and ensure we receive events
                    except Exception:
                        pass

                    # live_capture returns a generator of records
                    for rec in conn.live_capture():
                        if interrupted:
                            break
                        if not rec:
                            # library yields None periodically, keep alive
                            continue
                        # rec.user_id, rec.timestamp, rec.punch/status
                        ts = rec.timestamp
                        if ts and ts.tzinfo is None:
                            ts = timezone.make_aware(ts)
                        punch = getattr(rec, 'punch', getattr(rec, 'status', 0))
                        event_type = 'checkin' if punch in (0, 4) else 'checkout'
                        # Persist event and update last_seen
                        if device is None:
                            # If connecting by IP only, try to resolve device row
                            device = BiometricDevice.objects.filter(ip_address=ip).first()
                        company = device.company if device else None
                        _process_event(company, device, str(rec.user_id), event_type, ts, raw_payload={'source': 'live', 'raw': str(rec)})
                        if device:
                            device.last_seen = timezone.now()
                            device.is_active = True
                            device.save(update_fields=['last_seen', 'is_active'])
                            last_seen_time = time.time()
                        # Check for deactivation timeout
                        if device and last_seen_time:
                            if time.time() - last_seen_time > deactivation_timeout:
                                device.is_active = False
                                device.save(update_fields=['is_active'])
                                self.stdout.write(self.style.WARNING(f"Device {device.id} marked as inactive due to timeout."))
                                break
                finally:
                    try:
                        conn.disconnect()
                    except Exception:
                        pass
                # graceful exit
                if interrupted:
                    break
            except Exception as e:
                logger.exception('Live connection error: %s', e)
                time.sleep(int(options.get('reconnect_seconds') or 10))
                # On connection error, mark device as inactive
                if device:
                    device.is_active = False
                    device.save(update_fields=['is_active'])

        self.stdout.write(self.style.SUCCESS('Live capture stopped.'))

