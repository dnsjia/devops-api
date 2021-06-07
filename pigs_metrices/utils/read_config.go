package utils

import (
	"fmt"
	"github.com/spf13/viper"
	"log"
	"os"
)

var Conf = &Config{}


type HTTPConfig struct {
	Address string `mapstructure:"address"`
	Port    string `mapstructure:"port"`
	Token	string `mapstructure:"token"`
	ApiPort	string `mapstructure:"api_port"`
	AcceptHosts	string `mapstructure:"accept_hosts"`

}


type Server struct {
	HTTP          HTTPConfig      `mapstructure:"http"`
}


type Config struct {
	Server Server `mapstructure:"server"`
}


func ReadConfig(configDir string) Config {
	f, err := os.OpenFile("metrics_proxy.log", os.O_RDWR | os.O_CREATE | os.O_APPEND, 0666)

	if err != nil {
		fmt.Println(err)
		log.Fatalf("error opening file: %v", err)
	}
	defer f.Close()

	log.SetOutput(f)

	c := &Config{}
	filename := configDir

	viper.SetConfigType("yaml")
	viper.SetConfigFile(filename)

	err2 := viper.ReadInConfig()
	if err2 != nil {
		fmt.Println(err2)
		log.Fatalf("read config is failed err: %v", err2)
	}

	err = viper.Unmarshal(c)
	if err != nil {
		fmt.Println(err)
		log.Fatalf("unmarshal config is failed, err: %v", err)
	}
	return *c
}