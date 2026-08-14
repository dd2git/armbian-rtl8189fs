# RTL8189FS-WLAN für Armbian auf x96-Mini, Tanix TX3 Mini

Dieses Repository enthält ein getestetes Kernelmodul für den internen
Realtek-RTL8189FTV/RTL8189FS-SDIO-WLAN-Chip der Tanix TX3 Mini.

## Unterstütztes System

- Gerät: x96-Mini, Tanix TX3 Mini / Amlogic S905W
- Betriebssystem: Armbian OS auf Debian 12 Bookworm
- Kernel: **6.18.43-ophub**
- Architektur: ARM64 (`aarch64`)
- SDIO-ID: `024c:f179`
- Modul: `8189fs`, Treiberversion `v5.7.9_35795.20191128`

Das vorkompilierte Modul darf nur mit exakt demselben Kernel verwendet werden.
Das Installationsskript verweigert die Installation bei einer Abweichung.

## Installation auf einem zweiten Gerät

Zuerst den Kernel prüfen:

```bash
uname -r
```

Die Ausgabe muss `6.18.43-ophub` sein. Danach:

```bash
git clone https://github.com/dd2git/armbian-rtl8189fs.git
cd armbian-rtl8189fs
sudo ./install.sh
```

Nach erfolgreicher Installation werden Treiber und WLAN-Schnittstelle angezeigt.
Das Modul wird außerdem unter `/etc/modules-load.d/8189fs.conf` für folgende
Systemstarts aktiviert.

## WLAN-Netze suchen

```bash
./scan-wifi.sh
```

Alternativ:

```bash
nmcli device wifi list
```

## Mit einem WLAN verbinden

```bash
sudo nmcli device wifi connect "NAME-DES-WLANS" password "WLAN-PASSWORT" ifname wlan0
```

Das WLAN-Passwort gehört nicht in dieses Repository.

## Optionaler Einrichtungs-Hotspot

Der automatische WLAN-Einrichtungs-Hotspot befindet sich in einem eigenen
Repository: [dd2git/armbian-wifi-hotspot](https://github.com/dd2git/armbian-wifi-hotspot)

## Deinstallation

```bash
sudo ./uninstall.sh
```

Falls bei der Installation bereits ein gleichnamiges Modul vorhanden war, wird
es als `.backup` gesichert und bei der Deinstallation wiederhergestellt.


## Optional: GitHub-Release erzeugen

```bash
./create-release.sh
```

Dadurch entsteht `armbian-rtl8189fs-6.18.43-ophub.tar.gz`. Die Datei kann auf
GitHub unter **Releases → Draft a new release** als Anlage hochgeladen werden.

Installation aus einem Release-Archiv:

```bash
tar -xzf armbian-rtl8189fs-6.18.43-ophub.tar.gz
cd armbian-rtl8189fs-6.18.43-ophub
sudo ./install.sh
```

## Technischer Hintergrund und Neubau

Das Modul basiert auf dem Branch `rtl8189fs` aus:

<https://github.com/EvilOlaf/rtl8189ES_linux/tree/rtl8189fs>

Der verwendete Ophub-Kernel enthält zurückportierte `cfg80211`-APIs aus neueren
Kernelreihen. Deshalb wurden im Treiber in
`os_dep/linux/ioctl_cfg80211.c` die Versionsschwellen für die Anpassungen von
7.1/7.2 auf 6.18 gesetzt. Das Modul wurde mit der zum Kernel passenden ARM GNU
Toolchain 15.3 gebaut.

Nach jedem Kernelupdate muss das Modul für die neue Kernelversion neu gebaut
werden. Ein Modul für `6.18.43-ophub` darf nicht in eine andere Kernelversion
kopiert werden.

## Sicherheit

Dieses Repository enthält keine SSH-, Root- oder WLAN-Zugangsdaten. Prüfe vor
der Installation die Datei `SHA256SUMS` und veröffentliche niemals Passwörter in
Commits, Issues oder Release-Dateien.

## Lizenz

Die Skripte und der enthaltene Realtek-Treiber werden unter GPL-2.0-only
weitergegeben. Der Treiber basiert auf dem oben verlinkten Projekt.
