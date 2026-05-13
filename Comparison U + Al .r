library(ggplot2)

# Sample data - Al2O3 (wt%) and U (ppm)
data <- data.frame(
  sample = c("GK-2", "GK-3", "HH-1", "HH-2", "HH-3", 
             "KK-1", "KK-2", "KKF-1", "KKF-2", "KKF-3", "KKF-4", "KKF-5"),
  group = c("GK", "GK", "HH", "HH", "HH", 
            "KK", "KK", "KKF", "KKF", "KKF", "KKF", "KKF"),
  Al2O3 = c(5.2422, 6.3423, 9.1841, 4.9039, 7.0781,
            2.4449, 4.8967, 8.4659, 4.8450, 3.3062, 8.1666, 10.0037),
  U_ppm = c(NA, 8.0, 5.0, NA, NA,
            6.0, NA, NA, NA, NA, 20.0, NA)
)

# PAAS reference point
paas <- data.frame(
  sample = "PAAS",
  group = "PAAS",
  Al2O3 = 18.9,   # PAAS Al2O3 wt% - Taylor & McLennan 1985
  U_ppm = 3.1     # PAAS U ppm
)

# Group colours
group_colours <- c(
  "GK"  = "#D85A30",
  "HH"  = "#378ADD",
  "KK"  = "#534AB7",
  "KKF" = "#1D9E75"
)

# Remove NA rows for plotting
data_clean <- data[!is.na(data$U_ppm), ]

ggplot() +
  # Sample points
  geom_point(data = data_clean,
             aes(x = Al2O3, y = U_ppm, colour = group, label = sample),
             size = 4, shape = 16) +
  # Sample labels
  geom_text(data = data_clean,
            aes(x = Al2O3, y = U_ppm, label = sample, colour = group),
            vjust = -0.8, hjust = 0.5, size = 3.2, fontface = "plain") +
  # PAAS star
  geom_point(data = paas,
             aes(x = Al2O3, y = U_ppm),
             shape = 8, size = 4, colour = "#E8B000", stroke = 1.0) +
  geom_text(data = paas,
            aes(x = Al2O3, y = U_ppm, label = "PAAS"),
            vjust = -1.0, hjust = 0.5, size = 3.2,
            colour = "#E8B000", fontface = "plain") +
  # Scales and labels
  scale_colour_manual(values = group_colours, name = "Sample Group") +
  scale_x_continuous(limits = c(0, 22),
                     breaks = seq(0, 22, 2),
                     labels = function(x) paste0(x, "%")) +
  scale_y_continuous(limits = c(0, 25),
                     breaks = seq(0, 25, 5)) +
  labs(
    x = expression(Al[2]*O[3]~"(wt%)"),
    y = "U (ppm)",
    title = expression(Al[2]*O[3]~"vs U"),
    caption = "PAAS values from Taylor and McLennan (1985)\nSamples with U below detection limit excluded"
  ) +
  theme_bw() +
  theme(
    plot.title    = element_text(hjust = 0.5, size = 13, face = "bold"),
    axis.title    = element_text(size = 11),
    axis.text     = element_text(size = 10),
    legend.title  = element_text(size = 10, face = "bold"),
    legend.text   = element_text(size = 9),
    legend.position = "right",
    panel.grid.minor = element_blank(),
    plot.caption  = element_text(size = 8, colour = "grey50", hjust = 0)
  )