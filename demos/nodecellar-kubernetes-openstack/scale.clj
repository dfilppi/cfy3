      (coalesce
        (smap folds/count
           (with {:host nil :service "hostcount" :ttl 30} index)
        )
      )

      (where (not (nil? (riemann.index/lookup index nil "hostcount")))
        (fn [ev] (info "CNT " (:metric (riemann.index/lookup index nil "hostcount"))))
        (fn [ev] (info "HOST " (:host ev) " METRIC " (:metric ev)))
        (where (not (expired? event))
          (moving-time-window {{moving_window_size}}
            ;(combine folds/mean
            (smap folds/mean
              (fn [ev]
                (let [hostcnt (:metric (riemann.index/lookup index nil "hostcount"))
                      conns (/ (:metric ev) hostcnt)
                      cooling (not (nil? (riemann.index/lookup index "scaling" "suspended")))
                     ]
                   (if (and (not cooling) (< {{scale_threshold}} conns))
                     (do
                       (info "SCALE")
                       ;(process-policy-triggers ev)
                       (riemann.index/update index {:host "scaling" :service "suspended" :time (unix-time) :description "cooldown flag" :metric 0 :ttl {{cooldown_time}} :state "ok"})
                     )
                   )
                )
              )
            )
          )
        )
      )
