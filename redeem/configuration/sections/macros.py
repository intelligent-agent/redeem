from redeem.configuration.sections import BaseConfig


class MacrosConfig(BaseConfig):
    g29 = """
        M561                ; Reset the bed level matrix
        M558 P0             ; Set probe type to Servo with switch
        M557 P0 X10 Y20     ; Set probe point 0
        M557 P1 X10 Y180    ; Set probe point 1
        M557 P2 X180 Y100   ; Set probe point 2
        G28 X0 Y0           ; Home X Y

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P0 S            ; Probe point 0
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P1 S            ; Probe point 1
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 Z0              ; Home Z
        G0 Z12              ; Move Z up to allow space for probe
        G32                 ; Undock probe
        G92 Z0              ; Reset Z height to 0
        G30 P2 S            ; Probe point 2
        G0 Z0               ; Move the Z up
        G31                 ; Dock probe

        G28 X0 Y0           ; Home X Y
        """

    g31 = """
        M280 P0 S320 F3000  ; Probe up (Dock sled)
    """

    g32 = """
        M280 P0 S-60 F3000  ; Probe down (Undock sled)
    """
