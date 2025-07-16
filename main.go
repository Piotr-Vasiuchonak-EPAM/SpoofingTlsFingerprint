package main

import (
	"Golang/Request"
	"Golang/Response"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"github.com/Danny-Dasilva/CycleTLS/cycletls"
	"github.com/gorilla/mux"
	"io/ioutil"
	"log"
	"net/http"
	"net/http/cookiejar"
	url2 "net/url"
	"os"
	"strings"
)

func main() {
	port := "8000"
	if len(os.Args) > 1 {
		port = os.Args[1]
	}

	err := os.Setenv("tls13", "1")
	if err != nil {
		log.Println(err.Error())
	}

	router := mux.NewRouter()
	router.HandleFunc("/check-status", CheckStatus).Methods("GET")
	router.HandleFunc("/handle", Handle).Methods("POST")
	fmt.Println("The proxy server is running")
	log.Fatal(http.ListenAndServe(":"+port, router))
}

func CheckStatus(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode("good")
}

func Handle(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	var handleRequest Request.HandleRequest
	err := json.NewDecoder(r.Body).Decode(&handleRequest)
	if err != nil {
		http.Error(w, "invalid JSON request body", http.StatusBadRequest)
		return
	}

	client := cycletls.Init()

	// Prepare cookies
	var cookies []*http.Cookie
	for _, cookie := range handleRequest.Cookies {
		cookies = append(cookies, &http.Cookie{
			Name:     cookie.Name,
			Value:    cookie.Value,
			Path:     cookie.Path,
			Domain:   cookie.Domain,
			Expires:  cookie.Expires,
			MaxAge:   cookie.MaxAge,
			Secure:   cookie.Secure,
			HttpOnly: cookie.HTTPOnly,
		})
	}

	cookiesJar, _ := cookiejar.New(nil)
	requestUrl, _ := url2.Parse(handleRequest.Url)
	cookiesJar.SetCookies(requestUrl, cookies)

	opts := cycletls.Options{
		// Note: Danny-Dasilva CycleTLS doesn't have CookiesJar field,
		// so you might need to set cookies manually in Headers or handle differently.
		// Here we ignore CookiesJar since it's not defined in the new CycleTLS.
		InsecureSkipVerify: handleRequest.InsecureSkipVerify,
		Body:               handleRequest.Body,
		Proxy:              handleRequest.Proxy,
		Timeout:            handleRequest.Timeout,
		Headers:            handleRequest.Headers,
		Ja3:                handleRequest.Ja3,
		UserAgent:          handleRequest.UserAgent,
		DisableRedirect:    handleRequest.DisableRedirect,
	}

	resp, err := client.Do(handleRequest.Url, opts, handleRequest.Method)
	var handleResponse Response.HandleResponse
	if err != nil {
		fmt.Println(err)
		handleResponse.Success = false
		handleResponse.Error = err.Error()
		json.NewEncoder(w).Encode(handleResponse)
		return
	}

	handleResponse.Success = true
	handleResponse.Payload = &Response.HandleResponsePayload{
		Text:    decodeResponseBody(resp.Body, resp.Headers),
		Headers: resp.Headers,
		Status:  resp.Status,
		Url:     handleRequest.Url,
	}

	// Cookies: Danny-Dasilva CycleTLS doesn't expose cookies like Skyuzii's,
	// so this part depends on your Request/Response package compatibility.
	// Here, we skip adding cookies unless you implement manual cookie parsing.

	json.NewEncoder(w).Encode(handleResponse)
}

func decodeResponseBody(body string, headers map[string]string) string {
	if strings.EqualFold(headers["Content-Encoding"], "gzip") {
		reader, err := gzip.NewReader(strings.NewReader(body))
		if err != nil {
			// Return raw body if gzip decode fails
			return body
		}
		defer reader.Close()
		decoded, err := ioutil.ReadAll(reader)
		if err != nil {
			return body
		}
		return string(decoded)
	}
	return body
}
