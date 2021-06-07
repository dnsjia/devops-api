/*
Copyright © 2021 NAME HERE <EMAIL ADDRESS>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"fmt"
	"github.com/small-flying-pigs/metrics_proxy/utils"
	"github.com/spf13/cobra"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// proxyCmd represents the proxy command
var proxyCmd = &cobra.Command{
	Use:   "proxy",
	Short: "Run a proxy to the Kubernetes API server Metrics",
	Long: `
Creates a proxy server or application-level gateway between localhost and the Kubernetes API Server. It also allows
serving static content over specified HTTP path. All incoming data enters through one port and gets forwarded to the
Remote Kubernetes API Server Port and provides basic token authentication`,
	Args: cobra.MinimumNArgs(0),
	Run: func(cmd *cobra.Command, args []string) {
		config, err := cmd.Flags().GetString("config")
		if err != nil {
			fmt.Println("将使用默认配置")
		}

		f, err := os.OpenFile("metrics_proxy.log", os.O_RDWR | os.O_CREATE | os.O_APPEND, 0666)

		if err != nil {
			fmt.Println(err)
			log.Fatalf("error opening file: %v", err)
		}
		defer f.Close()

		log.SetOutput(f)

		file, _ := exec.LookPath(os.Args[0])
		path, _ := filepath.Abs(file)
		if runtime.GOOS == "windows" {
			path = strings.Replace(path, "\\", "/", -1)
		}
		i := strings.LastIndex(path, "/")
		defaultConfig := string(path[0 : i+1] + "metrics_proxy.yaml")

		if config == "" {
			fmt.Println("当前没有指定配置文件,将使用`pwd`/metrics_proxy.yaml")
			c := utils.ReadConfig(defaultConfig)

			_ = os.Setenv("metrics_proxy_address", c.Server.HTTP.Address)
			_ = os.Setenv("metrics_proxy_port", c.Server.HTTP.Port)
			_ = os.Setenv("metrics_proxy_token", c.Server.HTTP.Token)
			_ = os.Setenv("metrics_proxy_api_port", c.Server.HTTP.ApiPort)
			_ = os.Setenv("metrics_proxy_api_port", c.Server.HTTP.ApiPort)
			kubeAddress := "--address=" + c.Server.HTTP.Address
			kubePort := "--port=" + c.Server.HTTP.ApiPort
			acceptHosts := "--accept-hosts=" + c.Server.HTTP.AcceptHosts
			cmd := exec.Command("nohup","kubectl", "proxy", kubeAddress, kubePort, acceptHosts, ">/dev/null", "2>&1", "&")
			_ = cmd.Start()
			// _ = cmd.Wait()
			log.Printf("Process Pid: %v\n", cmd.Process.Pid)
			out, err := cmd.Output()
			log.Print(err)
			//out, kubeErr := exec.Command("nohup","kubectl", "proxy", kubeAddress, kubePort, ">/dev/null", "2>&1", "&")

			// as the out variable defined above is of type []byte we need to convert
			// this to a string or else we will see garbage printed out in our console
			// this is how we convert it to a string
			fmt.Println("Command Successfully Executed")
			output := string(out[:])
			log.Println(output)
			utils.RunProxy()

		}else {
			c := utils.ReadConfig(config)
			_ = os.Setenv("metrics_proxy_address", c.Server.HTTP.Address)
			_ = os.Setenv("metrics_proxy_port", c.Server.HTTP.Port)
			_ = os.Setenv("metrics_proxy_token", c.Server.HTTP.Token)
			_ = os.Setenv("metrics_proxy_api_port", c.Server.HTTP.ApiPort)
			kubeAddress := "--address=" + c.Server.HTTP.Address
			kubePort := "--port=" + c.Server.HTTP.ApiPort
			acceptHosts := "--accept-hosts=" + c.Server.HTTP.AcceptHosts
			cmd := exec.Command("nohup","kubectl", "proxy", kubeAddress, kubePort, acceptHosts, ">/dev/null", "2>&1", "&")
			_ = cmd.Start()
			// _ = cmd.Wait()
			log.Printf("Process Pid: %v\n", cmd.Process.Pid)
			out, err := cmd.Output()
			log.Println(err)
			fmt.Println("Command Successfully Executed")
			output := string(out[:])
			log.Println(output)
			utils.RunProxy()

		}
	},
}

func init() {
	rootCmd.AddCommand(proxyCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// proxyCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// proxyCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
	proxyCmd.Flags().StringP("config", "c", "","config file (default is $PWD/metrics_proxy.yaml)")
	//proxyCmd.Flags().StringVar(&cfgFile, "c", "", "config file (default is $HOME/.metrics_proxy.yaml)")
}
