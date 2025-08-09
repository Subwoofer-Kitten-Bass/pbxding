// SPDX-License-Identifier: MPL-2.0
// SPDX-FileCopyrightText: Copyright (c) 2024, Emir Aganovic
package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"os/signal"

	"github.com/emiago/diago"
	"github.com/emiago/diago/examples"
	"github.com/emiago/diago/testdata"
	"github.com/emiago/sipgo"
	"github.com/emiago/sipgo/sip"
)

// Dial this app with
// gophone dial -media=audio "sip:123@127.0.0.1"

type Config struct {
	Server   string
	Port     uint16
	Username string
	Password string
}

func main() {
	config := &Config{
		Server:   "sip:6127@sip.micropoc.de",
		Port:     5060,
		Username: "6127",
		Password: "814b96428a64",
	}

	flag.Parse()

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()

	examples.SetupLogger()

	err := start(ctx, config.Server, diago.RegisterOptions{
		Username: config.Username,
		Password: config.Password,
	})
	if err != nil {
		slog.Error("PBX finished with error", "error", err)
	}

	<-ctx.Done()
}

func start(ctx context.Context, recipientURI string, regOpts diago.RegisterOptions) error {
	recipient := sip.Uri{}
	if err := sip.ParseUri(recipientURI, &recipient); err != nil {
		return fmt.Errorf("failed to parse register uri: %w", err)
	}

	// Setup our main transaction user
	useragent := regOpts.Username
	if useragent == "" {
		useragent = "change-me"
	}

	ua, _ := sipgo.NewUA(
		sipgo.WithUserAgent(useragent),
		sipgo.WithUserAgentHostname("localhost"),
	)
	defer ua.Close()

	tu := diago.NewDiago(ua, diago.WithTransport(
		diago.Transport{
			Transport: "udp",
			BindHost:  "127.0.0.1",
			BindPort:  15060,
		},
	))

	// Start listening incoming calls
	go func() {
		tu.Serve(ctx, func(inDialog *diago.DialogServerSession) {
			slog.Info("New dialog request", "id", inDialog.ID)
			defer slog.Info("Dialog finished", "id", inDialog.ID)
			if err := Playback(inDialog); err != nil {
				slog.Error("Failed to play", "error", err)
			}
		})
	}()

	// Do register or fail on error
	return tu.Register(ctx, recipient, regOpts)
}

func Playback(inDialog *diago.DialogServerSession) error {
	inDialog.Trying()  // Progress -> 100 Trying
	inDialog.Ringing() // Ringing -> 180 Response
	inDialog.Answer()  // Answer -> 200 Response

	playfile, _ := testdata.OpenFile("tasse-lang.wav")
	slog.Info("Playing a file", "file", "tasse-lang.wav")

	pb, err := inDialog.PlaybackCreate()
	if err != nil {
		return err
	}
	_, err = pb.Play(playfile, "audio/wav")
	return err
}
