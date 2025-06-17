use strict;
use warnings;
use HTTP::Daemon;    # Moduł do tworzenia prostego serwera HTTP
use HTTP::Status;    # Zawiera standardowe kody odpowiedzi HTTP (np. RC_OK, RC_NOT_FOUND)

# Tworzy nowy serwer HTTP nasłuchujący na porcie 4321
my $d = HTTP::Daemon->new(LocalPort => 4321) || die "Nie można uruchomić serwera: $!";
print "Serwer działa pod adresem: ", $d->url, "\n";  # Wyświetla adres URL serwera

# Główna pętla oczekująca na połączenia klientów
while (my $c = $d->accept) {
    # Obsługuje każde żądanie HTTP od klienta w osobnej pętli
    while (my $r = $c->get_request) {
        # Obsługuje tylko żądania typu GET
        if ($r->method eq 'GET') {
            my $path = $r->url->path;   # Pobiera ścieżkę z URL-a (np. /index.html)
            $path =~ s|^/||;            # Usuwa początkowy ukośnik (np. "/index.html" → "index.html")
            $path = 'index.html' if $path eq '';  # Jeśli nie podano ścieżki, domyślnie "index.html"

            my $file = "./static/$path";  # Tworzy ścieżkę do pliku w katalogu "static"

            # Jeśli plik istnieje, wysyła jego zawartość jako odpowiedź
            if (-f $file) {
                $c->send_file_response($file);
            } else {
                # Jeśli pliku nie znaleziono, wysyła błąd 404 Not Found
                $c->send_error(RC_NOT_FOUND);
            }
        } else {
            # Jeśli metoda nie jest GET, wysyła błąd 403 Forbidden
            $c->send_error(RC_FORBIDDEN);
        }
    }
    # Po zakończeniu obsługi klienta zamyka połączenie
    $c->close;
    undef($c);
}
