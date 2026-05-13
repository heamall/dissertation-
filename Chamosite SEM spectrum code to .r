# ============================================================
#  EDS Spectra – KKF5  |  Bruker Esprit format
#  Labels snap to the actual spectral peak at each element line
# ============================================================

# install.packages("ggplot2")
library(ggplot2)

# ============================================================
# 1.  FILE LIST  –  change folder to where your .txt files live
# ============================================================

folder <- "."    # <-- e.g. "C:/Data/KKF5"
files  <- list.files(folder, pattern = "\\.txt$", full.names = TRUE)

# ============================================================
# 2.  ELEMENT LINE DEFINITIONS  (keV)
# ============================================================

common_lines <- data.frame(
  Element = c("O Ka",  "Fe La"),
  keV     = c(0.525,   0.705),
  stringsAsFactors = FALSE
)

mineral_lines <- list(
  hematite = data.frame(
    Element = c("Fe Ka", "Fe Kb"),
    keV     = c(6.404,   7.058),
    stringsAsFactors = FALSE
  ),
  chamosite = data.frame(
    Element = c("Mg Ka", "Al Ka", "Si Ka", "Fe Ka", "Fe Kb"),
    keV     = c(1.254,   1.487,   1.740,   6.404,   7.058),
    stringsAsFactors = FALSE
  ),
  quartz = data.frame(
    Element = c("Si Ka", "Al Ka"),
    keV     = c(1.740,   1.487),
    stringsAsFactors = FALSE
  ),
  bromine = data.frame(
    Element = c("Br La", "Br Ka"),
    keV     = c(1.480,   11.924),
    stringsAsFactors = FALSE
  )
)

# ============================================================
# 3.  HELPERS
# ============================================================

get_mineral <- function(fname) {
  f <- tolower(basename(fname))
  if (grepl("hematite",  f)) return("hematite")
  if (grepl("chamosite", f)) return("chamosite")
  if (grepl("quartz",    f)) return("quartz")
  if (grepl("_br\\b|_br\\.", f)) return("bromine")
  return("chamosite")
}

read_bruker <- function(path) {
  raw        <- readLines(path, warn = FALSE)
  data_start <- grep("^Energy\\s+Counts", raw)
  if (!length(data_start)) stop("No 'Energy Counts' header in: ", path)
  
  get_meta <- function(key) {
    ln <- raw[grep(paste0("^", key, ":"), raw)[1]]
    trimws(sub(paste0("^", key, ":\\s*"), "", ln))
  }
  lt <- tryCatch(get_meta("Life time"),      error = function(e) "?")
  kv <- tryCatch(get_meta("Primary energy"), error = function(e) "15")
  
  df <- read.table(
    text       = raw[(data_start + 1):length(raw)],
    header     = FALSE,
    col.names  = c("Energy_keV", "Counts"),
    colClasses = c("numeric", "numeric"),
    fill       = TRUE
  )
  df <- df[!is.na(df$Energy_keV) & !is.na(df$Counts), ]
  df <- subset(df, Energy_keV >= 0 & Counts >= 0)
  list(data = df, life_time = lt, kV = kv)
}

# Find the max counts within +/- window keV of each element line
snap_to_peak <- function(el_lines, df, window = 0.05) {
  el_lines$Counts <- sapply(el_lines$keV, function(k) {
    nearby <- df[abs(df$Energy_keV - k) <= window, ]
    if (nrow(nearby) == 0) return(NA_real_)
    max(nearby$Counts)
  })
  el_lines[!is.na(el_lines$Counts), ]
}

# ============================================================
# 4.  PLOT FUNCTION
# ============================================================

plot_spectrum <- function(path) {
  sp      <- read_bruker(path)
  df      <- sp$data
  mineral <- get_mineral(path)
  
  el_lines <- rbind(common_lines, mineral_lines[[mineral]])
  el_lines <- el_lines[!duplicated(el_lines$Element), ]
  el_lines <- subset(el_lines, keV <= min(max(df$Energy_keV), 15))
  el_lines <- snap_to_peak(el_lines, df)
  
  title    <- gsub("_", "  ", tools::file_path_sans_ext(basename(path)))
  subtitle <- sprintf("Bruker Esprit  |  %s kV  |  Life time: %s s", sp$kV, sp$life_time)
  
  pal      <- c(hematite = "#8b1a1a", chamosite = "#2e6b3e",
                quartz   = "#4e7fa8", bromine   = "#7a3b8c")
  fill_col <- pal[[mineral]]
  
  p <- ggplot(df, aes(x = Energy_keV, y = Counts)) +
    geom_area(fill = fill_col, alpha = 0.25) +
    geom_line(colour = fill_col, linewidth = 0.5)
  
  if (nrow(el_lines) > 0) {
    p <- p +
      geom_vline(
        data      = el_lines,
        aes(xintercept = keV),
        colour    = "#c0392b",
        linetype  = "dashed",
        linewidth = 0.45,
        alpha     = 0.8
      ) +
      geom_label(
        data          = el_lines,
        aes(x = keV, y = Counts, label = Element),
        vjust         = -0.4,
        colour        = "#c0392b",
        fill          = "white",
        size          = 2.8,
        fontface      = "bold",
        label.size    = 0.25,
        label.padding = unit(0.15, "lines")
      )
  }
  
  p <- p +
    labs(title = title, subtitle = subtitle,
         x = "Energy (keV)", y = "Counts") +
    coord_cartesian(xlim = c(0, 10),
                    ylim = c(0, max(df$Counts) * 1.25)) +
    theme_bw(base_size = 11) +
    theme(
      plot.title       = element_text(face = "bold", size = 11),
      plot.subtitle    = element_text(colour = "grey45", size = 8),
      panel.grid.minor = element_blank()
    )
  p
}

# ============================================================
# 5.  SAVE INDIVIDUAL PLOTS
# ============================================================

out_dir <- file.path(folder, "spectra_plots")
dir.create(out_dir, showWarnings = FALSE)

for (f in files) {
  message("Plotting: ", basename(f))
  p <- tryCatch(plot_spectrum(f), error = function(e) {
    message("  SKIPPED (", e$message, ")"); NULL
  })
  if (is.null(p)) next
  out_name <- paste0(tools::file_path_sans_ext(basename(f)), ".png")
  ggsave(file.path(out_dir, out_name), plot = p,
         width = 10, height = 5, dpi = 300)
}

# ============================================================
# 6.  COMBINED FACET PLOT
# ============================================================

all_data <- lapply(files, function(f) {
  sp <- tryCatch(read_bruker(f), error = function(e) NULL)
  if (is.null(sp)) return(NULL)
  df <- sp$data
  df$mineral <- get_mineral(f)
  df$label   <- gsub("_", " ", tools::file_path_sans_ext(basename(f)))
  df
})
all_data <- do.call(rbind, Filter(Negate(is.null), all_data))

# Build per-facet label data (peak-snapped, per spectrum)
label_data <- lapply(files, function(f) {
  sp <- tryCatch(read_bruker(f), error = function(e) NULL)
  if (is.null(sp)) return(NULL)
  df      <- sp$data
  mineral <- get_mineral(f)
  lbl     <- gsub("_", " ", tools::file_path_sans_ext(basename(f)))
  
  el <- rbind(common_lines, mineral_lines[[mineral]])
  el <- el[!duplicated(el$Element), ]
  el <- subset(el, keV <= min(max(df$Energy_keV), 15))
  el <- snap_to_peak(el, df)
  if (nrow(el) == 0) return(NULL)
  el$mineral <- mineral
  el$label   <- lbl
  el
})
label_data <- do.call(rbind, Filter(Negate(is.null), label_data))

pal <- c(hematite = "#8b1a1a", chamosite = "#2e6b3e",
         quartz   = "#4e7fa8", bromine   = "#7a3b8c")

p_combined <- ggplot(all_data, aes(x = Energy_keV, y = Counts,
                                   colour = mineral, fill = mineral)) +
  geom_area(alpha = 0.20) +
  geom_line(linewidth = 0.4) +
  geom_vline(
    data      = label_data,
    aes(xintercept = keV),
    colour    = "#c0392b", linetype = "dashed",
    linewidth = 0.35, alpha = 0.7
  ) +
  geom_label(
    data          = label_data,
    aes(x = keV, y = Counts, label = Element),
    vjust         = -0.4,
    colour        = "#c0392b",
    fill          = "white",
    size          = 1.8,
    fontface      = "bold",
    label.size    = 0.15,
    label.padding = unit(0.10, "lines")
  ) +
  facet_wrap(~ label, scales = "free_y", ncol = 3) +
  coord_cartesian(xlim = c(0, 10)) +
  scale_colour_manual(values = pal) +
  scale_fill_manual(values = pal) +
  labs(title    = "KKF5 - All EDS Spectra",
       subtitle = "y-axes free  |  x range 0-10 keV  |  labels at peak height",
       x = "Energy (keV)", y = "Counts",
       colour = "Mineral", fill = "Mineral") +
  theme_bw(base_size = 10) +
  theme(
    strip.text       = element_text(size = 7, face = "bold"),
    panel.grid.minor = element_blank(),
    legend.position  = "bottom"
  )


