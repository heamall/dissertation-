library(ggplot2)
library(ggrepel)

# Sample data - Al2O3 (wt%) and Ti (ppm)
data <- data.frame(
  sample = c("GK-2", "GK-3", "HH-1", "HH-2", "HH-3", 
             "KK-1", "KK-2", "KKF-1", "KKF-2", "KKF-3", "KKF-4", "KKF-5"),
  group = c("GK", "GK", "HH", "HH", "HH", 
            "KK", "KK", "KKF", "KKF", "KKF", "KKF", "KKF"),
  Al2O3 = c(5.2422, 6.3423, 9.1841, 4.9039, 7.0781,
            2.4449, 4.8967, 8.4659, 4.8450, 3.3062, 8.1666, 10.0037),
  Ti_ppm = c(1998.0, 2737.0, 1610.0, 1301.0, 4120.0,
             1468.0, 2343.0, 4052.0, 3365.0, 1157.0, 2518.0, 2587.0)
)

# PAAS reference point
paas <- data.frame(
  sample = "PAAS",
  Al2O3  = 18.9,
  Ti_ppm = 5577
)

# Group colours
group_colours <- c(
  "GK"  = "#D85A30",
  "HH"  = "#378ADD",
  "KK"  = "#534AB7",
  "KKF" = "#1D9E75"
)

ggplot() +
  # Sample points
  geom_point(data = data,
             aes(x = Al2O3, y = Ti_ppm, colour = group),
             size = 4, shape = 16) +
  # Repelled sample labels
  geom_text_repel(data = data,
                  aes(x = Al2O3, y = Ti_ppm, label = sample, colour = group),
                  size = 3.2,
                  box.padding = 0.4,
                  point.padding = 0.3,
                  segment.size = 0.3,
                  segment.colour = "grey60",
                  max.overlaps = Inf,
                  show.legend = FALSE) +
  # PAAS star
  geom_point(data = paas,
             aes(x = Al2O3, y = Ti_ppm),
             shape = 8, size = 4, colour = "#E8B000", stroke = 1) +
  geom_text_repel(data = paas,
                  aes(x = Al2O3, y = Ti_ppm, label = sample),
                  size = 3.2,
                  colour = "#E8B000",
                  fontface = "plain",
                  box.padding = 0.5,
                  point.padding = 0.3,
                  segment.size = 0.3,
                  segment.colour = "grey60",
                  show.legend = FALSE) +
  # Scales and labels
  scale_colour_manual(values = group_colours, name = "Sample Group") +
  scale_x_continuous(limits = c(0, 22),
                     breaks = seq(0, 22, 2),
                     labels = function(x) paste0(x, "%")) +
  scale_y_continuous(limits = c(0, 6500),
                     breaks = seq(0, 6500, 1000),
                     labels = function(x) format(x, big.mark = ",")) +
  labs(
    x       = expression(Al[2]*O[3]~"(wt%)"),
    y       = "Ti (ppm)",
    title   = expression(Al[2]*O[3]~"vs Ti"),
    caption = "PAAS values from Taylor and McLennan (1985)"
  ) +
  theme_bw() +
  theme(
    plot.title       = element_text(hjust = 0.5, size = 13, face = "bold"),
    axis.title       = element_text(size = 11),
    axis.text        = element_text(size = 10),
    legend.title     = element_text(size = 10, face = "bold"),
    legend.text      = element_text(size = 9),
    legend.position  = "right",
    panel.grid.minor = element_blank(),
    plot.caption     = element_text(size = 8, colour = "grey50", hjust = 0)
  )