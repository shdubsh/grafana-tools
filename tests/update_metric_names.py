import unittest

from update_metric_names import rewrite_expr, make_backwards_compatible


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
