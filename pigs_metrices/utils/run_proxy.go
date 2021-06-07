package utils

import (
	"bytes"
	"fmt"
	"github.com/ouqiang/goproxy"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

type EventHandler struct{}


func (e *EventHandler) Connect(ctx *goproxy.Context, rw http.ResponseWriter) {

}

func (e *EventHandler) Auth(ctx *goproxy.Context, rw http.ResponseWriter)  {

}

func (e *EventHandler) BeforeRequest(ctx *goproxy.Context) {

	if clientIP, _, err := net.SplitHostPort(ctx.Req.RemoteAddr); err == nil {
		if prior, ok := ctx.Req.Header["X-Forwarded-For"]; ok {
			clientIP = strings.Join(prior, ", ") + ", " + clientIP
		}
		ctx.Req.Header.Set("X-Forwarded-For", clientIP)
	}
	// 读取Body
	body, err := ioutil.ReadAll(ctx.Req.Body)
	if err != nil {
		// 错误处理
		return
	}
	// 鉴权认证 kubernetes api server
	log.Println(ctx.Req.Body)
	token := os.Getenv("metrics_proxy_token")
	log.Println(ctx.Req.Header)
	reqToken := ctx.Req.Header.Get("token")
	if  reqToken != token {
		log.Printf("认证失败，禁止登录")
		ctx.Abort()
		return
	}
	// Request.Body只能读取一次, 读取后必须再放回去
	// Response.Body同理
	ctx.Req.Body = ioutil.NopCloser(bytes.NewReader(body))
}

func (e *EventHandler) BeforeResponse(ctx *goproxy.Context, resp *http.Response, err error) {
	if err != nil {
		return
	}
	// 修改response
}

// 设置上级代理, 代理kubernetes api server
func (e *EventHandler) ParentProxy(req *http.Request) (*url.URL, error) {
	KubeApiAddress := os.Getenv("metrics_proxy_address")
	KubeApiPort := os.Getenv("metrics_proxy_api_port")
	proxyHost := "http://" + KubeApiAddress + ":" + KubeApiPort
	return url.Parse(proxyHost)
}

func (e *EventHandler) Finish(ctx *goproxy.Context) {
	log.Printf("请求结束 URL:%s\n", ctx.Req.URL)
}

// 记录错误日志
func (e *EventHandler) ErrorLog(err error) {

	log.Printf("%v", err)
}


func RunProxy() {
	f, err := os.OpenFile("metrics_proxy.log", os.O_RDWR | os.O_CREATE | os.O_APPEND, 0666)

	if err != nil {
		fmt.Println(err)
		log.Fatalf("error opening file: %v", err)
	}
	defer f.Close()

	log.SetOutput(f)

	proxy := goproxy.New(goproxy.WithDelegate(&EventHandler{}))
	// 反向代理后的监听端口
	listenPort := ":" + os.Getenv("metrics_proxy_port")

	server := &http.Server{
		Addr:        listenPort,
		Handler:      proxy,
		ReadTimeout:  1 * time.Minute,
		WriteTimeout: 1 * time.Minute,
	}
	log.Printf("The listening port is %v", listenPort)
	fmt.Printf("The listening port is %v", listenPort)
	ServerErr := server.ListenAndServe()
	if ServerErr != nil {
		panic(err)
	}

}