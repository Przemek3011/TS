use HTTP::Daemon;     # Moduł do tworzenia prostego serwera HTTP
use HTTP::Status;     # Zawiera standardowe kody statusów HTTP (np. RC_OK, RC_FORBIDDEN)

# Tworzy nowy serwer HTTP nasłuchujący na losowym porcie
my $d = HTTP::Daemon->new || die;  # Jeśli nie uda się uruchomić serwera, wypisuje błąd i kończy działanie

# Wyświetla adres URL serwera, np. http://localhost:xxxx/
print "Please contact me at: ", $d->url, "\n";

# Główna pętla nasłuchująca na połączenia od klientów
while (my $c = $d->accept) {
    # Obsługuje żądania HTTP od klienta
    while (my $r = $c->get_request) {
        # Obsługuje tylko żądania GET
        if ($r->method eq 'GET') {
            my $output = "";  # Zmienna na wynik końcowy (nagłówki HTTP)

            # Iteruje po wszystkich nagłówkach przesłanych w żądaniu
            foreach my $name ($r->header_field_names) {
                $output .= "$name: " . $r->header($name) . "\n";  # Dołącza nazwę i wartość nagłówka do odpowiedzi
            }

            # Wysyła odpowiedź HTTP 200 OK z nagłówkami jako treść w formacie tekstowym
            $c->send_response(
                HTTP::Response->new(
                    RC_OK,                    # Kod statusu 200 OK
                    undef,                    # Brak dodatkowego komunikatu
                    ['Content-Type' => 'text/plain'],  # Nagłówek: typ treści to tekst zwykły
                    $output                   # Treść odpowiedzi — nagłówki HTTP klienta
                )
            );
        }
        else {
            # Jeśli żądanie nie jest typu GET, odrzuca je z kodem 403 Forbidden
            $c->send_error(RC_FORBIDDEN);
        }
    }

    # Zamyka połączenie z klientem po przetworzeniu wszystkich żądań
    $c->close;
    undef($c);  # Czyści zmienną, zwalniając zasoby
}
