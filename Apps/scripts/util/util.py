import re

def add_tfoot_to_html_table(html_table: str) -> str:
    """Ensure the HTML table has a <tfoot> for column filtering."""
    if "<tfoot>" in html_table:
        return html_table
    m = re.search(r"<thead>(.*?)</thead>", html_table, flags=re.DOTALL)
    if not m:
        return html_table
    headers = m.group(1)
    return html_table.replace("</table>", f"<tfoot>{headers}</tfoot></table>")


def get_datatables_dependencies():
    """Return common DataTables JS/CSS + dark theme overrides."""
    return """
    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">

    <!-- jQuery + DataTables -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

    <!-- Dark theme for DataTables -->
    <style>
        .dataTables_wrapper .dataTables_filter label,
        .dataTables_wrapper .dataTables_info,
        .dataTables_wrapper .dataTables_paginate { color: #fff; }

        .dataTables_paginate .paginate_button { color: #fff !important; }
        .dataTables_paginate .paginate_button.current {
            background:#444 !important; color:white !important;
        }
        .dataTables_length label, .dataTables_length select {
            color:#fff!important; background:#1f1f1f!important;
        }
        table.dataTable thead th { color:#80cbc4; }
    </style>
    """


def get_datatables_init_script(selector: str) -> str:
    """Return JS initializer for DataTables with column search boxes."""
    return f"""
    <script>
    $(document).ready(function() {{
        var table = $('{selector}').DataTable({{
            lengthMenu: [[10,25,50,-1],[10,25,50,"All"]],
            pageLength: 25,
            order: [],
            orderMulti: true,
            searching: true,
            paging: true,
            info: true
        }});

        // Add search boxes per column
        $('{selector} tfoot th').each(function() {{
            $(this).html('<input type="text" placeholder="Search" style="width:100%;font-size:11px;">');
        }});

        table.columns().every(function() {{
            var that = this;
            $('input', this.footer()).on('keyup change clear', function() {{
                if (that.search() !== this.value) {{
                    that.search(this.value).draw();
                }}
            }});
        }});
    }});
    </script>
    """


#shared dark style for all reports
dark_style = """
<style>
body {
    background-color: #121212;
    color: #e0e0e0;
    font-family: Arial, sans-serif;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
th, td {
    border: 1px solid #444;
    padding: 8px;
    text-align: center;
}
th {
    background-color: #1f1f1f;
    color: #e0e0e0;
}
tr:nth-child(even) {
    background-color: #1a1a1a;
}
tr:hover {
    background-color: #333;
}
h2 { margin-top: 30px; }

.dataTables_wrapper .dataTables_length,
.dataTables_wrapper .dataTables_filter,
.dataTables_wrapper .dataTables_info,
.dataTables_wrapper .dataTables_paginate {
    color: #e0e0e0;
}

.dataTables_wrapper .dataTables_filter input {
    background-color: #222;
    color: white;
    border: 1px solid #555;
    padding: 4px;
}

.dataTables_wrapper .dataTables_paginate .paginate_button {
    background: #444 !important;
    border: 1px solid #666;
    color: white !important;
}

tfoot input {
    width: 100%;
    background-color: #222;
    color: #fff;
    border: 1px solid #555;
}
</style>
"""