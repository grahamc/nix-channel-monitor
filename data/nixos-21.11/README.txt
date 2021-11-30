                    This service is provided for free.

                    If you use this service automatically please be
                    polite and follow some rules:

                      - please don't poll any more often than every 15
                        minutes, to reduce the traffic to my server.

                      - please don't poll exactly on a 5 minute
                        increment, to avoid the "thundering herd"
                        problem.

                      - please add a delay on your scheduled polling
                        script for a random delay between 1 and 59
                        seconds, to further spread out  the load.

                      - please consider using my webhooks instead:
                        email me at graham at grahamc dot com or
                        message gchristensen on #nixos on Freenode.


                    FILE NOTES

                      Each format comes with two files, a "latest" file
                      and a "history" file.

                      The history files will retain 100000 lines of history.



                    FORMAT NOTES

                        latest, history:
                          commit-hash date-of-commit

                        latest-v2, history-v2:
                          commit-hash date-of-commit date-of-advancement

                        latest-url, history-url:
                          channel-url date-of-advancement

                      Note: "date-of-advancement" is actually the date
                      the advancement was _detected_, and can be
                      wildly wrong for no longer updated channels. For
                      example, the nixos-13.10 channel's
                      date-of-advancement is quite recent despite the
                      channel not having updated in many years.

                      All three formats will continue to be updated.

                    Thank you, good luck, have fun
                    Graham
