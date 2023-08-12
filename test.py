from nicegui import ui

with ui.grid(columns=2):
    ui.label('Name:').classes('col-span-2')
    ui.label('Tom')

    ui.label('Age:')
    ui.label('42')

    ui.label('Height:')
    ui.label('1.80m')

ui.run()