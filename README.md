# Asynchroner I/O mit Python

In diesem Repository finden Sie den in c’t !!!/2023, S. !!! besprochenen Python-Code: [1.py](artikel/1.py), [2.py](artikel/2.py), [3.py](artikel/3.py) und [4.py](artikel/4.py) spiegeln die Entwicklungsschritte wider, [nanodirb.py](artikel/nanodirb.py) ist der abgedruckte rudimentäre Dirb-Klon und [dirb.py](dirb.py) die asynchron funktionierende Nachimplementierung (nicht 1:1) des originalen [Dirb](https://manpages.debian.org/bullseye/dirb/dirb.1.en.html).

## Vorbereiten

```bash
git clone https://github.com/ct-Open-Source/asiopy.git
cd asiopy
pipenv install
```

## Benutzen

Zum Beispiel:

```
pipenv run ./dirb.py "http://example.com" \
  -w path-list1.txt -w path-list2.txt \
  -n 10
  -f \
  --csv \
  -o scan-result.csv
```

Wobei `http://example.com` die Basis-URL des zu scannenden Dienstes ist. Die Pfade in den mit `-w` angegebenen Dateien (ein Pfad pro Zeile) werden beim Scannen an die Basis-URL angehängt.

Der Schalter `-n` gibt an, wie viel Worker parallel arbeiten sollen, also wie viel Scanvorgänge gleichzeitig ablaufen sollen (Vorgabe: 10).

Mit dem Schalter `--csv` produziert das Skript eine Ausgabe im CSV-Format, die sich zum Einlesen in Tabellenkalkulationen eignet.

Für manche URLs liefern Webserver einen Redirect zurück (HTTP-Status-Code 301 oder 302). Ohne den Schalter `-f` empfängt das Skript nur den Redirect, mit dem Schalter folgt es ihm zu der URL, auf die der Redirect umleitet.

Per Default landen die Ergebnisse in der Standardausgabe. Der Schalter `-o` lenkt sie in eine Datei um.

Die Eingabe von `dirb.py -h` listet alle möglichen Kommandozeilenoptionen auf.


## Lizenz

Siehe [LICENSE](LICENSE)


## Copyright

Copyright ©️ 2023 [Oliver Lau](mailto:ola@ct.de), [Heise Medien GmbH & Co. KG](https://www.heise-gruppe.de/artikel/Heise-Medien-3904998.html)


## Nutzungshinweise

Diese Software wurde zu Lehr- und Demonstrationszwecken geschaffen und ist nicht für den produktiven Einsatz vorgesehen. Heise Medien und der Autor haften daher nicht für Schäden, die aus der Nutzung der Software entstehen, und übernehmen keine Gewähr für ihre Vollständigkeit, Fehlerfreiheit und Eignung für einen bestimmten Zweck.
