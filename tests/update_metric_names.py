import unittest

from update_metric_names import rewrite_expr, make_backwards_compatible, update_scaling, cleanup_duplicate, update_query_parameters


class Update_Metric_Names(unittest.TestCase):
    def test_rewrite_expr_simple_metric(self):
        self.assertEqual(
            rewrite_expr('node_memory_Cached{instance=~\"$instance:.*\"}'),
            'node_memory_Cached_bytes{instance=~\"$instance:.*\"}'
        )

    def test_rewrite_expr_complex_metric(self):
        # Note the whitespace at the end
        self.assertEqual(
            rewrite_expr('node_memory_MemTotal{instance=~\"$instance:.*\"} - node_memory_Cached{instance=~\"$instance:.*\"} - node_memory_Buffers{instance=~\"$instance:.*\"} - node_memory_MemFree{instance=~\"$instance:.*\"} '),
            'node_memory_MemTotal_bytes{instance=~\"$instance:.*\"} - node_memory_Cached_bytes{instance=~\"$instance:.*\"} - node_memory_Buffers_bytes{instance=~\"$instance:.*\"} - node_memory_MemFree_bytes{instance=~\"$instance:.*\"} '
        )

    def test_make_backwards_compatible_wrapped_function(self):
        self.assertEqual(
            make_backwards_compatible(
                'irate(node_network_transmit_bytes_total{instance=~\'$hypervisor.*\',device=~\'e.*\'}[5m])*8',
                'irate(node_network_transmit_bytes{instance=~\'$hypervisor.*\',device=~\'e.*\'}[5m])*8'),
            '(irate(node_network_transmit_bytes_total{instance=~\'$hypervisor.*\',device=~\'e.*\'}[5m])*8) or (irate(node_network_transmit_bytes{instance=~\'$hypervisor.*\',device=~\'e.*\'}[5m])*8)'
        )

    def test_backwards_compatible_simple_metric(self):
        self.assertEqual(
            make_backwards_compatible(
                'node_memory_Cached_bytes{instance=~\"$instance:.*\"}',
                'node_memory_Cached{instance=~\"$instance:.*\"}'),
            'node_memory_Cached_bytes{instance=~\"$instance:.*\"} or node_memory_Cached{instance=~\"$instance:.*\"}'
        )

    def test_backwards_compatible_unwrapped_function(self):
        self.assertEqual(
            make_backwards_compatible(
                'irate(node_disk_writes_completed_total{instance=~\'$instance:.*\', device=~\"[vsh]d[a-z]\"}[5m])',
                'irate(node_disk_writes_completed{instance=~\'$instance:.*\', device=~\"[vsh]d[a-z]\"}[5m])'
            ),
            'irate(node_disk_writes_completed_total{instance=~\'$instance:.*\', device=~\"[vsh]d[a-z]\"}[5m]) or irate(node_disk_writes_completed{instance=~\'$instance:.*\', device=~\"[vsh]d[a-z]\"}[5m])'
        )

    def test_backwards_compatible_complex_wrapped(self):
        self.assertEqual(
            make_backwards_compatible(
                '100.0 - 100 * (node_filesystem_avail_bytes{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'} / node_filesystem_size_bytes{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'})',
                '100.0 - 100 * (node_filesystem_avail{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'} / node_filesystem_size{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'})'
            ),
            '(100.0 - 100 * (node_filesystem_avail_bytes{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'} / node_filesystem_size_bytes{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'})) or (100.0 - 100 * (node_filesystem_avail{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'} / node_filesystem_size{instance=~\'$instance:.*\',device !~\'tmpfs\',device!~\'by-uuid\'}))'
        )

    def test_cleanup_duplicate(self):
        self.assertEqual(
            cleanup_duplicate(
                'irate(node_disk_io_time_seconds_total{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m])irate(node_disk_io_time_seconds_total{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m])'
            ),
            'irate(node_disk_io_time_seconds_total{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m])'
        )

    def test_update_scaling_basic(self):
        self.assertEqual(
            'node_disk_io_time_seconds_total{instance=~"$server.*"} * 1000',
            update_scaling(
                'node_disk_io_time_ms',
                'node_disk_io_time_ms{instance=~"$server.*"}'
            )
        )

    def test_update_scaling_wrapped(self):
        self.assertEqual(
            'irate(node_disk_io_time_seconds_total{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m]) * 1000',
            update_scaling(
                'node_disk_io_time_ms',
                'irate(node_disk_io_time_ms{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m])'
            )
        )

    def test_update_scaling_scaled(self):
        self.assertEqual(
            'irate(node_disk_io_time_seconds_total{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m])',
            update_scaling(
                'node_disk_io_time_ms',
                'irate(node_disk_io_time_ms{instance=~"$server:.*",device=~"[vs]d[a-z]+"}[5m]) / 1000'
            )
        )
        self.assertEqual(
            'irate(node_disk_io_time_seconds_total{instance=~"$node"}[5m])*100',
            update_scaling(
                'node_disk_io_time_ms',
                'irate(node_disk_io_time_ms{instance=~"$node"}[5m])/10')
        )

    def test_update_scaling_complex(self):
        self.assertEqual(
            '100 * (irate(node_disk_io_time_seconds_total{instance=~"graphite.*",device=~"[vs]d[a-z]+"}[5m])) > 0',
            update_scaling(
                'node_disk_io_time_ms',
                '100 * (irate(node_disk_io_time_ms{instance=~"graphite.*",device=~"[vs]d[a-z]+"}[5m]) / 1000) > 0'
            )
        )
        self.assertEqual(
            'max(irate(node_disk_read_time_seconds_total{instance="$server:9100", device=~"sda.*"}[5m]) * 1000)',
            update_scaling(
                'node_disk_read_time_ms',
                'max(irate(node_disk_read_time_ms{instance="$server:9100", device=~"sda.*"}[5m]))'
            )
        )

    def test_update_query_parameters_simple(self):
        self.assertEqual(
            'sum by (mode)(irate(node_cpu_seconds_total{cpu="0",mode="steal",instance=~"$node:$port",job=~"$job"}[5m])) * 100',
            update_query_parameters(
                'node_cpu',
                'sum by (mode)(irate(node_cpu{cpu="cpu0",mode=\'steal\',instance=~"$node:$port",job=~"$job"}[5m])) * 100'
            )
        )

    def test_update_query_parameters_guest(self):
        self.assertEqual(
            'sum by (mode)(irate(node_cpu_guest_seconds_total{cpu="0",mode="user",instance=~"$node:$port",job=~"$job"}[5m])) * 100',
            update_query_parameters(
                'node_cpu',
                'sum by (mode)(irate(node_cpu{cpu="cpu0",mode=\'guest\',instance=~"$node:$port",job=~"$job"}[5m])) * 100'
            )
        )

    def test_update_query_parameters_guest_nice(self):
        self.assertEqual(
            'sum by (mode)(irate(node_cpu_guest_seconds_total{cpu="0",mode="nice",instance=~"$node:$port",job=~"$job"}[5m])) * 100',
            update_query_parameters(
                'node_cpu',
                'sum by (mode)(irate(node_cpu{cpu="cpu0",mode=\'guest_nice\',instance=~"$node:$port",job=~"$job"}[5m])) * 100'
            )
        )

    def test_update_query_parameters_nfs(self):
        self.assertEqual(
            'node_nfs_requests_total{method="Access",proto="3"}',
            update_query_parameters(
                'node_nfs_procedures',
                'node_nfs_procedures{procedure="Access",version="3"}'
            )
        )

    def test_update_query_parameters_already_backwards_compatible(self):
        self.assertEqual(
            '(sum by (mode)(irate(node_cpu_guest_seconds_total{cpu="0",mode="nice",instance=~"$node:$port",job=~"$job"}[5m])) * 100) or sum by (mode)(irate(node_cpu{cpu="cpu0",mode=\'guest_nice\',instance=~"$node:$port",job=~"$job"}[5m])) * 100',
            update_query_parameters(
                'node_cpu',
                '(sum by (mode)(irate(node_cpu_guest_seconds_total{cpu="0",mode="nice",instance=~"$node:$port",job=~"$job"}[5m])) * 100) or sum by (mode)(irate(node_cpu{cpu="cpu0",mode=\'guest_nice\',instance=~"$node:$port",job=~"$job"}[5m])) * 100'
            )
        )
