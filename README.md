# Tugas Besar 1 IF3130 : Implementasi Protokol TCP-like Go-Back-N

Dibuat untuk memenuhi Tugas Besar 1 IF3130 Jaringan Komputer.

## Daftar Isi

- [Deskripsi Program](#deskripsi-program)
- [Fitur Program](#fitur-program)
- [How To Use](#how-to-use)
- [Authors](#authors)

## Deskripsi Program

Merupakan suatu program sederhana memanfaatkan _socket programming_ untuk mengimplementasikan protokol TCP-like. Selain itu, digunakan mekanisme pengiriman _automatic repeat request_ (ARQ) Go Back N

## Fitur Program

1. Mampu mengirimkan data atau file dari _server_ ke banyak _client_ memanfaatkan protokol TCP-like dan algoritma Go Back N
2. Optimasi manajemen memori dengan memanfaatkan _seek_
3. Dukungan pengiriman metadata file kepada _client_
4. Kemampuan paralelisasi pada _server_ 
5. Implementasi algoritma _hamming code_ 7 bit (_Unintegrated with program_) 
6. Permainan _tic-tac-toe_ sederhana memanfaatkan protokol yang telah dibuat (_Unfinished_) 

## How To Use

1. Clone _repository_ ini dengan perintah

    ```bash
    git clone https://github.com/Sister20/tugas-besar-if3130-jaringan-komputer-amn-cabang-k2.git
    ```

2. Untuk menggunakan program, nyalakan _server_ terlebih dahulu dengan perintah

    ```bash
    python server.py [broadcast_port] [pathfile_input]
    ```
    
    Catatan: broadcast_port merupakan port yang akan di-listen oleh server. Pastikan bahwa file berada pada folder test

3. Anda dapat memilih untuk mengaktifkan fitur paralelisasi pada _server_ atau tidak

4. Aktifkan _client_ dengan menggunakan perintah

    ```bash
    python client.py [client_port] [broadcast_port] [pathfile_output]
    ```
    
    Catatan: broadcast_port merupakan port yang di-listen oleh server. File output akan diletakkan pada folder out

5. _Server_ dapat menerima _request_ dari banyak _client_ sekaligus. Ketika sudah siap, _server_ akan melakukan _file transfer_ kepada setiap _client_ yang ada

5. Anda dapat menjalankan perintah

    ```bash
    python server.py -h
    ```

    atau

    ```bash
    python client.py -h
    ```

    Untuk melihat panduan lebih lengkap

## Authors

| Name                           |   NIM    |
| ------------------------------ | :------: |
| Go Dillon Audris               | 13521062 |
| Austin Gabriel Pardosi         | 13521084 |
| Michael Leon Putra Widhi       | 13521108 |